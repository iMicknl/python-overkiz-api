"""Generate a device catalog from the Overkiz reference API.

Fetches all available reference data:
- Device type definitions per protocol (commands, states, attributes, manufacturer refs)
- Controllable definitions with discrete state values and data properties
- Reference metadata (controllable types, UI classes, widgets, classifiers, protocols)

Outputs JSON files and a browsable docs page.

Usage:
    OVERKIZ_USERNAME=... OVERKIZ_PASSWORD=... uv run utils/generate_device_catalog.py
    OVERKIZ_USERNAME=... OVERKIZ_PASSWORD=... uv run utils/generate_device_catalog.py --server somfy_europe
"""

# ruff: noqa: T201

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from pyoverkiz.auth.credentials import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import Server
from pyoverkiz.models import (
    DeviceSearchResult,
    DeviceTypeDefinition,
    ValuePrototype,
)

OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "device-catalog"
DOCS_DIR = Path(__file__).parent.parent / "docs"


def _serialize_value_prototype(vp: ValuePrototype) -> dict:
    """Serialize a ValuePrototype to dict, including all non-None fields."""
    result: dict = {"type": vp.type}
    if vp.min_value is not None:
        result["minValue"] = vp.min_value
    if vp.max_value is not None:
        result["maxValue"] = vp.max_value
    if vp.enum_values:
        result["enumValues"] = vp.enum_values
    if vp.description:
        result["description"] = vp.description
    return result


def device_type_to_dict(dt: DeviceTypeDefinition) -> dict:
    """Serialize a DeviceTypeDefinition to a plain dict for JSON output."""
    result: dict = {
        "typeId": dt.type_id,
        "subsystemId": dt.subsystem_id,
        "localPairing": dt.local_pairing,
        "uiClass": dt.ui_class,
        "uiWidget": dt.ui_widget,
        "uiProfiles": dt.ui_profiles,
        "uiClassifiers": dt.ui_classifiers,
        "controllableName": dt.controllable_name,
        "controllableType": dt.controllable_type,
        "protocolType": dt.protocol_type,
    }

    if dt.commands:
        result["commands"] = [
            {
                "commandName": cmd.command_name,
                "nparams": cmd.nparams,
                **({"description": cmd.description} if cmd.description else {}),
                **(
                    {
                        "parameters": [
                            {
                                "optional": p.optional,
                                "sensitive": p.sensitive,
                                "valuePrototypes": [
                                    _serialize_value_prototype(vp)
                                    for vp in p.value_prototypes
                                ],
                            }
                            for p in cmd.prototype.parameters
                        ]
                    }
                    if cmd.prototype and cmd.prototype.parameters
                    else {}
                ),
                **(
                    {"protocolSpecifics": cmd.protocol_specifics}
                    if cmd.protocol_specifics
                    else {}
                ),
            }
            for cmd in dt.commands
        ]

    if dt.states:
        result["states"] = [
            {
                "name": state.name,
                **({"type": state.type} if state.type else {}),
                "eventBased": state.event_based,
                "persistent": state.persistent,
                **(
                    {
                        "valuePrototypes": [
                            _serialize_value_prototype(vp)
                            for vp in state.prototype.value_prototypes
                        ]
                    }
                    if state.prototype and state.prototype.value_prototypes
                    else {}
                ),
                **(
                    {"protocolSpecifics": state.protocol_specifics}
                    if state.protocol_specifics
                    else {}
                ),
            }
            for state in dt.states
        ]

    if dt.attributes:
        result["attributes"] = [
            {
                "name": attr.name,
                **({"type": attr.type} if attr.type is not None else {}),
                **(
                    {"defaultValue": attr.default_value}
                    if attr.default_value is not None
                    else {}
                ),
                **(
                    {"protocolSpecifics": attr.protocol_specifics}
                    if attr.protocol_specifics
                    else {}
                ),
            }
            for attr in dt.attributes
        ]

    if dt.manufacturer_references:
        result["manufacturerReferences"] = [
            {
                "provider": ref.provider,
                "tags": [
                    {"tag": t.tag, **({"type": t.type} if t.type else {})}
                    for t in ref.tags
                ],
            }
            for ref in dt.manufacturer_references
        ]

    return result


def _dedupe_device_types(devices: list[dict]) -> list[dict]:
    """Deduplicate device types that share the same interface.

    Entries with the same uiClass, controllableType, commands and states are
    considered duplicates (they differ only by subsystemId or typeId).
    Returns one representative entry per unique interface, with a collected
    list of all typeIds from the duplicates stored in '_typeIds'.
    """
    seen: dict[tuple, dict] = {}
    for d in devices:
        cmds = tuple(sorted(c["commandName"] for c in d.get("commands", [])))
        states = tuple(sorted(s["name"] for s in d.get("states", [])))
        key = (d.get("uiClass"), d.get("controllableType"), cmds, states)
        if key not in seen:
            entry = dict(d)
            entry["_typeIds"] = [d.get("typeId")]
            seen[key] = entry
        else:
            type_id = d.get("typeId")
            if type_id not in seen[key]["_typeIds"]:
                seen[key]["_typeIds"].append(type_id)
    return list(seen.values())


def _find_controllable_definition(
    device: dict,
    proto_prefix: str,
    definitions: dict[str, dict],
) -> dict | None:
    """Find the controllable definition matching a device entry."""
    widget = device.get("uiWidget", "")
    ui_class = device.get("uiClass", "")
    candidates = []
    if widget:
        candidates.append(f"{proto_prefix}:{widget}Component")
        candidates.append(f"{proto_prefix}:{widget}")
    if ui_class and ui_class != widget:
        candidates.append(f"{proto_prefix}:{ui_class}Component")
        candidates.append(f"{proto_prefix}:{ui_class}")
    for name in candidates:
        if name in definitions:
            return definitions[name]
    return None


def generate_docs_page(
    catalog_data: dict,
    definitions: dict[str, dict] | None = None,
) -> None:
    """Generate a browsable markdown docs page for device types.

    Uses catalog data from /reference/devices/search as the primary source,
    grouped by protocol. Entries are deduplicated by interface (same uiClass,
    controllableType, commands and states).
    """
    protocols: dict[str, list[dict]] = catalog_data.get("protocols", {})
    if definitions is None:
        definitions = {}

    lines = [
        "---",
        "hide:",
        "  - toc",
        "---",
        "",
        "# Device Types",
        "",
        "This page lists all known device types from the Overkiz API, "
        "grouped by protocol. Each entry shows the commands it accepts and the states "
        "it exposes.",
        "",
        "!!! note",
        "    This page is auto-generated from the Overkiz API. "
        "Run `uv run utils/generate_device_catalog.py` to regenerate.",
        "",
    ]

    # Deduplicate per protocol
    deduped: dict[str, list[dict]] = {}
    total_count = 0
    for proto_name in sorted(protocols.keys()):
        unique = _dedupe_device_types(protocols[proto_name])
        unique.sort(key=lambda d: (d.get("uiClass", ""), d.get("controllableType", "")))
        deduped[proto_name] = unique
        total_count += len(unique)

    lines.append(
        f"**{len(deduped)} protocols**, "
        f"**{total_count} unique device types** documented below."
    )
    lines.append("")

    # Table of contents by protocol
    lines.append("## Protocols")
    lines.append("")
    for proto_name in sorted(deduped.keys()):
        count = len(deduped[proto_name])
        anchor = proto_name.lower().replace(" ", "-")
        lines.append(f"- [{proto_name}](#{anchor}) ({count} types)")
    lines.append("")

    # Per-protocol sections
    for proto_name in sorted(deduped.keys()):
        devices = deduped[proto_name]
        proto_prefix = proto_name.lower()
        lines.append(f"## {proto_name}")
        lines.append("")
        lines.append(f"{len(devices)} device types.")
        lines.append("")

        for device in devices:
            ui_class = device.get("uiClass", "Unknown")
            ctrl_type = device.get("controllableType", "")
            widget = device.get("uiWidget", "")
            commands = device.get("commands", [])
            states = device.get("states", [])
            profiles = device.get("uiProfiles", [])
            type_ids = device.get("_typeIds", [])

            # Look up the controllable definition for enrichment
            ctrl_name = device.get("controllableName", "")
            ctrl_def = definitions.get(ctrl_name) if ctrl_name else None
            if not ctrl_def:
                ctrl_def = _find_controllable_definition(
                    device, proto_prefix, definitions
                )

            if widget and widget != ui_class:
                title = f"{ui_class}/{widget}"
            else:
                title = ui_class
            summary = f"{title} ({ctrl_type})"
            summary += f" — {len(commands)} commands, {len(states)} states"

            lines.append(f'??? note "{summary}"')
            lines.append("")

            # Metadata
            meta_parts = []
            if type_ids:
                meta_parts.append(
                    f"**Type IDs:** {', '.join(f'`{t}`' for t in type_ids)}"
                )
            if ctrl_name:
                meta_parts.append(f"**Controllable:** `{ctrl_name}`")
            if profiles:
                meta_parts.append(
                    f"**Profiles:** {', '.join(f'`{p}`' for p in profiles)}"
                )
            if meta_parts:
                lines.append(f"    {' | '.join(meta_parts)}")
                lines.append("")

            # Data properties (from controllable definition)
            if ctrl_def and ctrl_def.get("dataProperties"):
                data_props = ctrl_def["dataProperties"]
                lines.append("    **Data Properties**")
                lines.append("")
                for dp in data_props:
                    dp_name = dp.get("qualifiedName", "?")
                    dp_value = dp.get("value", "")
                    lines.append(f"    - `{dp_name}` = `{dp_value}`")
                lines.append("")

            # Commands table
            if commands:
                lines.append("    **Commands**")
                lines.append("")
                lines.append("    | Command | Parameters | Notes |")
                lines.append("    |---------|-----------|-------|")
                for cmd in commands:
                    cmd_name = cmd.get("commandName", "?")
                    nparams = cmd.get("nparams", 0)
                    param_info = ""
                    if cmd.get("parameters"):
                        parts = []
                        for p in cmd["parameters"]:
                            flags = []
                            if p.get("optional"):
                                flags.append("optional")
                            if p.get("sensitive"):
                                flags.append("🔒sensitive")
                            flag_str = f" ({', '.join(flags)})" if flags else ""
                            for vp in p.get("valuePrototypes", []):
                                vp_type = vp.get("type", "")
                                if vp.get("enumValues"):
                                    parts.append(
                                        f"{vp_type}: "
                                        f"{', '.join(str(v) for v in vp['enumValues'][:5])}"
                                        f"{flag_str}"
                                    )
                                elif (
                                    vp.get("minValue") is not None
                                    and vp.get("maxValue") is not None
                                ):
                                    parts.append(
                                        f"{vp_type} [{vp['minValue']}..{vp['maxValue']}]"
                                        f"{flag_str}"
                                    )
                                elif vp_type:
                                    parts.append(f"{vp_type}{flag_str}")
                            if not p.get("valuePrototypes") and flags:
                                parts.append(flag_str.strip())
                        param_info = "; ".join(parts) if parts else f"{nparams} params"
                    elif nparams > 0:
                        param_info = f"{nparams} params"

                    notes_parts = []
                    if cmd.get("description"):
                        desc = (
                            cmd["description"]
                            .replace("\n", " ")
                            .replace("|", "\\|")
                            .strip()
                        )
                        notes_parts.append(desc)
                    if cmd.get("protocolSpecifics"):
                        specs = cmd["protocolSpecifics"]
                        for spec in specs[:2]:
                            cluster = spec.get("cluster_id", "")
                            if cluster != "":
                                notes_parts.append(f"cluster:{cluster}")
                    notes = "; ".join(notes_parts)
                    lines.append(f"    | `{cmd_name}` | {param_info} | {notes} |")
                lines.append("")

            # States table
            if states:
                # Build lookup for discrete values from controllable definition
                ctrl_state_values: dict[str, list[str]] = {}
                if ctrl_def:
                    for cs in ctrl_def.get("states", []):
                        qn = cs.get("qualifiedName", "")
                        if cs.get("values") and qn:
                            # Map short name (e.g. "OnOffState") to values
                            short = qn.split(":")[-1] if ":" in qn else qn
                            ctrl_state_values[short] = cs["values"]

                lines.append("    **States**")
                lines.append("")
                lines.append("    | State | Type | Range / Values | Notes |")
                lines.append("    |-------|------|----------------|-------|")
                for state in states:
                    s_name = state.get("name", "?")
                    s_type = state.get("type", "")
                    range_info = ""
                    if state.get("valuePrototypes"):
                        parts = []
                        for vp in state["valuePrototypes"]:
                            if vp.get("enumValues"):
                                parts.append(
                                    ", ".join(str(v) for v in vp["enumValues"][:5])
                                )
                            elif (
                                vp.get("minValue") is not None
                                and vp.get("maxValue") is not None
                            ):
                                parts.append(f"[{vp['minValue']}..{vp['maxValue']}]")
                        range_info = "; ".join(parts)

                    # Enrich with discrete values from controllable definition
                    if not range_info and s_name in ctrl_state_values:
                        range_info = ", ".join(ctrl_state_values[s_name])

                    notes_parts = []
                    if state.get("protocolSpecifics"):
                        specs = state["protocolSpecifics"]
                        for spec in specs[:2]:
                            cluster = spec.get("cluster_id", "")
                            if cluster != "":
                                notes_parts.append(f"cluster:{cluster}")
                    notes = "; ".join(notes_parts)
                    lines.append(
                        f"    | `{s_name}` | {s_type} | {range_info} | {notes} |"
                    )
                lines.append("")

        lines.append("")

    output_path = DOCS_DIR / "device-types.md"
    output_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"✓ Generated docs page: {output_path}")


async def fetch_device_catalog(server: Server) -> None:
    """Fetch full device catalog from the API."""
    username = os.environ["OVERKIZ_USERNAME"]
    password = os.environ["OVERKIZ_PASSWORD"]

    async with OverkizClient(
        server=server,
        credentials=UsernamePasswordCredentials(username, password),
    ) as client:
        await client.login()

        # --- Reference metadata ---

        # Controllable types (ACTUATOR, SENSOR, etc.)
        print("Fetching /reference/controllableTypes...")
        controllable_types = await client.get_reference_controllable_types()
        print(f"  Found {len(controllable_types)} controllable types")

        # UI reference lists
        print("Fetching UI reference lists...")
        ui_classes = await client.get_reference_ui_classes()
        ui_widgets = await client.get_reference_ui_widgets()
        ui_classifiers = await client.get_reference_ui_classifiers()
        print(
            f"  Classes: {len(ui_classes)}, "
            f"Widgets: {len(ui_widgets)}, "
            f"Classifiers: {len(ui_classifiers)}"
        )

        # Protocol types
        protocol_types = await client.get_reference_protocol_types()
        print(f"  Protocols: {len(protocol_types)}")

        # --- Device type catalog (per protocol) ---

        all_device_types: dict[str, list[dict]] = {}
        total_count = 0

        for proto in protocol_types:
            print(f"\nFetching devices for protocol: {proto.name} ({proto.prefix})...")

            payload = {
                "protocolTypes": [proto.name],
                "withCommands": True,
                "withStates": True,
                "withAttributes": True,
                "withManufacturerReferences": True,
            }

            result: DeviceSearchResult = await client.search_reference_devices(payload)
            device_count = len(result.devices_types)
            total_count += device_count

            if not result.all_result:
                print(f"  WARNING: Response truncated for {proto.name}!")

            print(f"  Found {device_count} device types")

            if result.devices_types:
                all_device_types[proto.name] = [
                    device_type_to_dict(dt) for dt in result.devices_types
                ]

        # Also try fetching without protocol filter to catch any missed
        print("\nFetching all devices without protocol filter...")
        payload_all = {
            "withCommands": True,
            "withStates": True,
            "withAttributes": True,
            "withManufacturerReferences": True,
        }
        result_all = await client.search_reference_devices(payload_all)
        print(f"  Found {len(result_all.devices_types)} total device types")
        if not result_all.all_result:
            print("  WARNING: Response truncated!")

        # --- Controllable definitions ---

        # Collect controllable names directly from search results
        all_controllable_names: set[str] = set()
        for proto_devices in all_device_types.values():
            for d in proto_devices:
                name = d.get("controllableName")
                if name:
                    all_controllable_names.add(name)

        # Add names from user's setup
        try:
            controllables = await client.get_device_controllables()
            all_controllable_names.update(controllables.keys())
        except Exception as e:
            print(f"  Could not fetch setup controllables: {e}")

        devices = await client.get_devices()
        for device in devices:
            all_controllable_names.add(device.controllable_name)

        print(f"\nFound {len(all_controllable_names)} unique controllable names")

        # Fetch individual controllable definitions
        total_candidates = len(all_controllable_names)
        print(f"\nFetching controllable definitions ({total_candidates} candidates)...")
        definitions_data: dict[str, dict] = {}
        not_found: list[str] = []
        for i, name in enumerate(sorted(all_controllable_names), 1):
            if i % 50 == 0 or i == total_candidates:
                print(
                    f"  [{i}/{total_candidates}] "
                    f"found: {len(definitions_data)}, "
                    f"not found: {len(not_found)}"
                )
            try:
                definition = await client.get_reference_controllable(name)
                definitions_data[name] = definition
            except Exception:
                not_found.append(name)

        print(f"  Done — found: {len(definitions_data)}, not found: {len(not_found)}")

        # --- Write outputs ---
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Full catalog JSON (used by generate_enums.py for command/param enrichment)
        catalog_data = {
            "server": server.name,
            "totalDeviceTypes": total_count,
            "protocols": all_device_types,
        }
        catalog_path = OUTPUT_DIR / "device_catalog.json"
        catalog_path.write_text(
            json.dumps(catalog_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\n✓ Written catalog to {catalog_path}")

        # Reference metadata JSON
        reference_data = {
            "server": server.name,
            "controllableTypes": controllable_types,
            "uiClasses": ui_classes,
            "uiWidgets": ui_widgets,
            "uiClassifiers": ui_classifiers,
            "protocolTypes": [
                {"id": p.id, "prefix": p.prefix, "name": p.name, "label": p.label}
                for p in protocol_types
            ],
        }
        reference_path = OUTPUT_DIR / "reference_metadata.json"
        reference_path.write_text(
            json.dumps(reference_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"✓ Written reference metadata to {reference_path}")

        # Controllable names list (resolved names only)
        names_path = OUTPUT_DIR / "controllable_names.txt"
        names_path.write_text(
            "\n".join(sorted(definitions_data.keys())), encoding="utf-8"
        )
        print(f"✓ Written {len(definitions_data)} controllable names to {names_path}")

        # Controllable definitions JSON
        definitions_path = OUTPUT_DIR / "controllable_definitions.json"
        definitions_path.write_text(
            json.dumps(definitions_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"✓ Written {len(definitions_data)} definitions to {definitions_path}")

        # Generate browsable docs page
        generate_docs_page(catalog_data, definitions_data)

        # Summary
        summary_lines = [
            f"Device Catalog Summary — Server: {server.name}",
            "=" * 60,
            f"Total protocols: {len(protocol_types)}",
            f"Total device types (by protocol): {total_count}",
            f"Total device types (unfiltered): {len(result_all.devices_types)}",
            f"Controllable types: {len(controllable_types)}",
            f"UI classes: {len(ui_classes)}",
            f"UI widgets: {len(ui_widgets)}",
            f"UI classifiers: {len(ui_classifiers)}",
            f"Controllable definitions found: {len(definitions_data)}",
            f"Controllable names not resolved: {len(not_found)}",
            "",
            "Controllable Types:",
            *[
                f"  {ct['name']} (id={ct['id']}, label={ct['label']})"
                for ct in controllable_types
            ],
            "",
            "Protocols:",
            *[
                f"  {proto.name} ({proto.prefix}): "
                f"{len(all_device_types.get(proto.name, []))} device types"
                for proto in protocol_types
            ],
        ]
        summary_text = "\n".join(summary_lines)
        summary_path = OUTPUT_DIR / "summary.txt"
        summary_path.write_text(summary_text, encoding="utf-8")
        print(f"✓ Written summary to {summary_path}")

        print(f"\n{summary_text}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    server_choices = [s.value for s in Server]
    parser = argparse.ArgumentParser(
        description="Generate a device catalog from the Overkiz API."
    )
    parser.add_argument(
        "--server",
        choices=server_choices,
        default=Server.SOMFY_EUROPE.value,
        help=f"Server to connect to (default: {Server.SOMFY_EUROPE.value})",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(fetch_device_catalog(Server(args.server)))
