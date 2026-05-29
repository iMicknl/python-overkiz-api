"""Generate device catalog documentation from per-server JSON files.

Reads all server data from docs/data/*.json (produced by
fetch_server_data.py), merges them, and generates the device-types.md docs page.

No API calls are made — this works entirely offline.

Usage:
    uv run utils/generate_device_catalog.py
"""

# ruff: noqa: T201

from __future__ import annotations

import json
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "docs"
SERVERS_DIR = Path(__file__).parent.parent / "docs" / "data"


def _dedupe_device_types(devices: list[dict]) -> list[dict]:
    """Deduplicate device types that share the same interface.

    Entries with the same uiClass, controllableType, commands and states are
    considered duplicates (they differ only by subsystemId or typeId).
    Returns one representative entry per unique interface, with a collected
    list of all typeIds and servers from the duplicates.
    """
    seen: dict[tuple, dict] = {}
    for d in devices:
        cmds = tuple(sorted(c["commandName"] for c in d.get("commands", [])))
        states = tuple(sorted(s["name"] for s in d.get("states", [])))
        key = (d.get("uiClass"), d.get("controllableType"), cmds, states)
        if key not in seen:
            entry = dict(d)
            entry["_typeIds"] = [d.get("typeId")]
            entry["_servers"] = [d.get("_server")] if d.get("_server") else []
            seen[key] = entry
        else:
            type_id = d.get("typeId")
            if type_id not in seen[key]["_typeIds"]:
                seen[key]["_typeIds"].append(type_id)
            server = d.get("_server")
            if server and server not in seen[key]["_servers"]:
                seen[key]["_servers"].append(server)
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


def load_merged_data() -> tuple[dict, dict[str, dict]]:
    """Load all per-server JSON files and merge into a unified catalog.

    Returns a tuple of (merged_catalog_data, merged_definitions).
    """
    merged_protocols: dict[str, list[dict]] = {}
    merged_definitions: dict[str, dict] = {}
    servers_found: list[str] = []

    if not SERVERS_DIR.exists():
        return {"protocols": {}, "servers": []}, {}

    for server_file in sorted(SERVERS_DIR.glob("*.json")):
        data = json.loads(server_file.read_text(encoding="utf-8"))
        server_name = data.get("server", server_file.stem)
        servers_found.append(server_name)

        for proto_name, devices in data.get("protocols", {}).items():
            if proto_name not in merged_protocols:
                merged_protocols[proto_name] = []
            for device in devices:
                device["_server"] = server_name
            merged_protocols[proto_name].extend(devices)

        for name, definition in data.get("controllableDefinitions", {}).items():
            if name not in merged_definitions:
                merged_definitions[name] = definition
            else:
                existing = merged_definitions[name]
                existing_richness = len(existing.get("states", [])) + len(
                    existing.get("commands", [])
                )
                new_richness = len(definition.get("states", [])) + len(
                    definition.get("commands", [])
                )
                if new_richness > existing_richness:
                    merged_definitions[name] = definition

    return {
        "servers": servers_found,
        "protocols": merged_protocols,
    }, merged_definitions


def generate_docs_page(
    catalog_data: dict,
    definitions: dict[str, dict],
) -> None:
    """Generate a browsable markdown docs page for device types."""
    protocols: dict[str, list[dict]] = catalog_data.get("protocols", {})

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
            _render_device_entry(lines, device, proto_prefix, definitions)

        lines.append("")

    output_path = DOCS_DIR / "device-types.md"
    output_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"✓ Generated {output_path}")


def _render_device_entry(
    lines: list[str],
    device: dict,
    proto_prefix: str,
    definitions: dict[str, dict],
) -> None:
    """Render a single device type entry as a collapsible markdown section."""
    ui_class = device.get("uiClass", "Unknown")
    ctrl_type = device.get("controllableType", "")
    widget = device.get("uiWidget", "")
    commands = device.get("commands", [])
    states = device.get("states", [])
    profiles = device.get("uiProfiles", [])
    type_ids = device.get("_typeIds", [])

    ctrl_name = device.get("controllableName", "")
    ctrl_def = definitions.get(ctrl_name) if ctrl_name else None
    if not ctrl_def:
        ctrl_def = _find_controllable_definition(device, proto_prefix, definitions)

    title = f"{ui_class}/{widget}" if widget and widget != ui_class else ui_class
    summary = f"{title} ({ctrl_type})"
    summary += f" — {len(commands)} commands, {len(states)} states"

    lines.append(f'??? note "{summary}"')
    lines.append("")

    # Metadata
    meta_parts = []
    if type_ids:
        meta_parts.append(f"**Type IDs:** {', '.join(f'`{t}`' for t in type_ids)}")
    servers = device.get("_servers", [])
    if servers:
        meta_parts.append(f"**Servers:** {', '.join(f'`{s}`' for s in servers)}")
    if ctrl_name:
        meta_parts.append(f"**Controllable:** `{ctrl_name}`")
    if profiles:
        meta_parts.append(f"**Profiles:** {', '.join(f'`{p}`' for p in profiles)}")
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
        _render_commands_table(lines, commands)

    # States table
    if states:
        _render_states_table(lines, states, ctrl_def)


def _render_commands_table(lines: list[str], commands: list[dict]) -> None:
    """Render the commands table for a device entry."""
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
                    flags.append("sensitive")
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
                            f"{vp_type} [{vp['minValue']}..{vp['maxValue']}]{flag_str}"
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
            desc = cmd["description"].replace("\n", " ").replace("|", "\\|").strip()
            notes_parts.append(desc)
        if cmd.get("protocolSpecifics"):
            specs = cmd["protocolSpecifics"]
            for spec in specs[:2]:
                cluster = spec.get("clusterId", "")
                if cluster != "":
                    notes_parts.append(f"cluster:{cluster}")
        notes = "; ".join(notes_parts)
        lines.append(f"    | `{cmd_name}` | {param_info} | {notes} |")
    lines.append("")


def _render_states_table(
    lines: list[str], states: list[dict], ctrl_def: dict | None
) -> None:
    """Render the states table for a device entry."""
    # Build lookup for discrete values from controllable definition
    ctrl_state_values: dict[str, list[str]] = {}
    if ctrl_def:
        for cs in ctrl_def.get("states", []):
            qn = cs.get("qualifiedName", "")
            if cs.get("values") and qn:
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
                    parts.append(", ".join(str(v) for v in vp["enumValues"][:5]))
                elif vp.get("minValue") is not None and vp.get("maxValue") is not None:
                    parts.append(f"[{vp['minValue']}..{vp['maxValue']}]")
            range_info = "; ".join(parts)

        if not range_info and s_name in ctrl_state_values:
            range_info = ", ".join(ctrl_state_values[s_name])

        notes_parts = []
        if state.get("protocolSpecifics"):
            specs = state["protocolSpecifics"]
            for spec in specs[:2]:
                cluster = spec.get("clusterId", "")
                if cluster != "":
                    notes_parts.append(f"cluster:{cluster}")
        notes = "; ".join(notes_parts)
        lines.append(f"    | `{s_name}` | {s_type} | {range_info} | {notes} |")
    lines.append("")


if __name__ == "__main__":
    catalog_data, definitions = load_merged_data()
    if not catalog_data.get("protocols"):
        print("No server data found in docs/data/")
        print("Run `uv run utils/fetch_server_data.py` first.")
        raise SystemExit(1)

    generate_docs_page(catalog_data, definitions)

    servers = catalog_data["servers"]
    protos = len(catalog_data["protocols"])
    print(f"\nMerged {len(servers)} servers: {', '.join(servers)}")
    print(f"Total: {protos} protocols, {len(definitions)} definitions")
