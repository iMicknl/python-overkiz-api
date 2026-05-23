"""Generate a device catalog by querying all protocols via /reference/devices/search.

Fetches full device type definitions for every protocol supported by the server,
including commands (with parameter prototypes), states, attributes and manufacturer
references. Outputs a JSON catalog, a controllable names list, and a docs page.

Usage:
    OVERKIZ_USERNAME=... OVERKIZ_PASSWORD=... uv run utils/generate_device_catalog.py
    OVERKIZ_USERNAME=... OVERKIZ_PASSWORD=... uv run utils/generate_device_catalog.py --server somfy_europe
"""

# ruff: noqa: T201, PLR2004

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from pyoverkiz.auth.credentials import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import Server
from pyoverkiz.models import DeviceSearchResult, DeviceTypeDefinition, ValuePrototype

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


def generate_docs_page(
    catalog_data: dict,
    controllable_definitions: dict[str, dict],
) -> None:
    """Generate a browsable markdown docs page for device types."""
    protocols = catalog_data.get("protocols", {})

    lines = [
        "---",
        "hide:",
        "  - toc",
        "---",
        "",
        "# Device Types",
        "",
        "This page lists all known device types (controllables) from the Overkiz API, "
        "grouped by protocol. Each entry shows the commands it accepts and the states it exposes.",
        "",
        "!!! note",
        "    This page is auto-generated from the Overkiz API. Run `uv run utils/generate_device_catalog.py` to regenerate.",
        "",
    ]

    # Summary stats
    total_types = sum(len(dts) for dts in protocols.values())
    lines.append(
        f"**{len(protocols)} protocols**, **{total_types} device types**, "
        f"**{len(controllable_definitions)} controllable definitions** documented below."
    )
    lines.append("")

    # Table of contents by protocol
    lines.append("## Protocols")
    lines.append("")
    for proto_name in sorted(protocols.keys()):
        device_types = protocols[proto_name]
        lines.append(
            f"- [{proto_name}](#{proto_name.lower()}) ({len(device_types)} types)"
        )
    lines.append("")

    # Per-protocol sections
    for proto_name in sorted(protocols.keys()):
        device_types = protocols[proto_name]
        lines.append(f"## {proto_name}")
        lines.append("")
        lines.append(f"{len(device_types)} device types.")
        lines.append("")

        for dt in sorted(device_types, key=lambda d: d.get("uiClass", "") or ""):
            ui_class = dt.get("uiClass") or "Unknown"
            ui_widget = dt.get("uiWidget") or ""
            ctrl_type = dt.get("controllableType") or ""
            type_id = dt.get("typeId")

            heading = f"{ui_class}"
            if ui_widget and ui_widget != ui_class:
                heading += f" ({ui_widget})"

            lines.append(f"### {heading}")
            lines.append("")

            # Metadata badges
            meta_parts = []
            if ctrl_type:
                meta_parts.append(f"**Type:** {ctrl_type}")
            if type_id is not None:
                meta_parts.append(f"**ID:** {type_id}")
            if dt.get("localPairing"):
                meta_parts.append("**Local pairing:** Yes")
            if dt.get("uiProfiles"):
                meta_parts.append(
                    f"**Profiles:** {', '.join(f'`{p}`' for p in dt['uiProfiles'])}"
                )
            if meta_parts:
                lines.append(" | ".join(meta_parts))
                lines.append("")

            # Commands table
            commands = dt.get("commands", [])
            if commands:
                lines.append("#### Commands")
                lines.append("")
                lines.append("| Command | Parameters | Description |")
                lines.append("|---------|-----------|-------------|")
                for cmd in commands:
                    cmd_name = cmd["commandName"]
                    desc = (
                        (cmd.get("description") or "")
                        .replace("|", "\\|")
                        .replace("\n", " ")
                    )
                    params = ""
                    if "parameters" in cmd:
                        param_parts = []
                        for p in cmd["parameters"]:
                            flags = []
                            if p.get("optional"):
                                flags.append("optional")
                            if p.get("sensitive"):
                                flags.append("sensitive")
                            for vp in p.get("valuePrototypes", []):
                                vp_str = f"`{vp['type'].lower()}`"
                                if "minValue" in vp and "maxValue" in vp:
                                    vp_str += f" ({vp['minValue']}\N{EN DASH}{vp['maxValue']})"
                                elif "minValue" in vp:
                                    vp_str += f" (\N{GREATER-THAN OR EQUAL TO} {vp['minValue']})"
                                elif "maxValue" in vp:
                                    vp_str += (
                                        f" (\N{LESS-THAN OR EQUAL TO} {vp['maxValue']})"
                                    )
                                if "enumValues" in vp:
                                    vals = ", ".join(
                                        f"`{v}`" for v in vp["enumValues"][:5]
                                    )
                                    if len(vp["enumValues"]) > 5:
                                        vals += ", \N{HORIZONTAL ELLIPSIS}"
                                    vp_str += f" — {vals}"
                                if flags:
                                    vp_str += f" *({', '.join(flags)})*"
                                param_parts.append(vp_str)
                        params = ", ".join(param_parts)
                    lines.append(f"| `{cmd_name}` | {params} | {desc} |")
                lines.append("")

            # States table
            states = dt.get("states", [])
            if states:
                lines.append("#### States")
                lines.append("")
                lines.append("| State | Type | Event-based | Persistent |")
                lines.append("|-------|------|-------------|------------|")
                for state in states:
                    state_name = state["name"]
                    state_type = state.get("type", "")
                    event_based = "\N{CHECK MARK}" if state.get("eventBased") else ""
                    persistent = "\N{CHECK MARK}" if state.get("persistent") else ""

                    type_info = state_type
                    for vp in state.get("valuePrototypes", []):
                        vp_type = vp.get("type", "").lower()
                        if "minValue" in vp and "maxValue" in vp:
                            type_info = f"{vp_type} ({vp['minValue']}\N{EN DASH}{vp['maxValue']})"
                        elif "enumValues" in vp:
                            vals = ", ".join(f"`{v}`" for v in vp["enumValues"][:5])
                            if len(vp["enumValues"]) > 5:
                                vals += ", \N{HORIZONTAL ELLIPSIS}"
                            type_info = f"{vp_type} — {vals}"
                        else:
                            type_info = vp_type

                    lines.append(
                        f"| `{state_name}` | {type_info} | {event_based} | {persistent} |"
                    )
                lines.append("")

            # Attributes
            attributes = dt.get("attributes", [])
            if attributes:
                lines.append("#### Attributes")
                lines.append("")
                lines.append("| Attribute | Default |")
                lines.append("|-----------|---------|")
                for attr in attributes:
                    default = attr.get("defaultValue", "")
                    lines.append(f"| `{attr['name']}` | {default} |")
                lines.append("")

        lines.append("---")
        lines.append("")

    # Controllable definitions section
    if controllable_definitions:
        lines.append("## Controllable Definitions")
        lines.append("")
        lines.append(
            "These are the specific controllable names (device types) fetched from "
            "`/reference/controllable/{name}`. Each maps to a combination of commands, "
            "states, UI class and widget."
        )
        lines.append("")

        for name in sorted(controllable_definitions.keys()):
            defn = controllable_definitions[name]
            lines.append(f"### {name}")
            lines.append("")

            ui_class = defn.get("uiClass", "")
            widget = defn.get("widgetName", "")
            ctrl_type = defn.get("type", "")
            meta = []
            if ui_class:
                meta.append(f"**UI Class:** `{ui_class}`")
            if widget:
                meta.append(f"**Widget:** `{widget}`")
            if ctrl_type:
                meta.append(f"**Type:** {ctrl_type}")
            if defn.get("uiProfiles"):
                meta.append(
                    f"**Profiles:** {', '.join(f'`{p}`' for p in defn['uiProfiles'])}"
                )
            if meta:
                lines.append(" | ".join(meta))
                lines.append("")

            commands = defn.get("commands", [])
            if commands:
                cmd_names = [c["commandName"] for c in commands]
                lines.append(f"**Commands:** {', '.join(f'`{c}`' for c in cmd_names)}")
                lines.append("")

            states = defn.get("states", [])
            if states:
                state_names = [
                    s.get("qualifiedName", s.get("name", "?")) for s in states
                ]
                lines.append(f"**States:** {', '.join(f'`{s}`' for s in state_names)}")
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

        # Get all protocol types to iterate over
        protocol_types = await client.get_reference_protocol_types()
        print(f"Found {len(protocol_types)} protocol types")

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

        # Get controllable names from setup
        print("\nFetching controllables from setup...")
        try:
            controllables = await client.get_device_controllables()
            print(f"  Found {len(controllables)} controllable names in setup")
        except Exception as e:
            print(f"  Could not fetch controllables: {e}")
            controllables = {}

        # Collect all controllable names
        all_controllable_names: set[str] = set()
        devices = await client.get_devices()
        for device in devices:
            all_controllable_names.add(device.controllable_name)
        all_controllable_names.update(controllables.keys())

        # Fetch individual controllable definitions
        print(f"\nFetching {len(all_controllable_names)} controllable definitions...")
        definitions_data: dict[str, dict] = {}
        for name in sorted(all_controllable_names):
            try:
                definition = await client.get_reference_controllable(name)
                definitions_data[name] = definition
            except Exception as e:
                print(f"  ! Could not fetch definition for {name}: {e}")

        # Write outputs
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

        # Controllable names list
        names_path = OUTPUT_DIR / "controllable_names.txt"
        names_path.write_text(
            "\n".join(sorted(all_controllable_names)), encoding="utf-8"
        )
        print(
            f"✓ Written {len(all_controllable_names)} controllable names to {names_path}"
        )

        # Controllable definitions JSON
        definitions_path = OUTPUT_DIR / "controllable_definitions.json"
        definitions_path.write_text(
            json.dumps(definitions_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"✓ Written {len(definitions_data)} definitions to {definitions_path}")

        # Generate browsable docs page
        generate_docs_page(catalog_data, definitions_data)

        # Summary
        print(f"\n{'=' * 60}")
        print(f"Server: {server.name}")
        print(f"Protocols: {len(protocol_types)}")
        print(f"Device types (by protocol): {total_count}")
        print(f"Device types (unfiltered): {len(result_all.devices_types)}")
        print(f"Controllable names: {len(all_controllable_names)}")
        print(f"Controllable definitions fetched: {len(definitions_data)}")


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
