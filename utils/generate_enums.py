"""Generate enum files from per-server reference data.

Reads all server data from docs/data/*.json (produced by
fetch_server_data.py) and generates enum source files and docs.

No API calls are made — this works entirely offline.

Usage:
    uv run utils/generate_enums.py
"""

# ruff: noqa: T201

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path

SERVERS_DIR = Path(__file__).parent.parent / "docs" / "data"
ENUMS_DIR = Path(__file__).parent.parent / "pyoverkiz" / "enums"
DOCS_DIR = Path(__file__).parent.parent / "docs"
FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures" / "setup"

# Hardcoded protocols that may not be available on all servers
ADDITIONAL_PROTOCOLS: list[tuple[str, str, int | None, str | None]] = [
    ("HLRR_WIFI", "hlrrwifi", None, None),
    ("RTN", "rtn", None, None),
]

# Hardcoded widgets that may not be available on all servers
ADDITIONAL_WIDGETS = [
    "AlarmPanelController",
    "CyclicGarageDoor",
    "CyclicSlidingGateOpener",
    "CyclicSwingingGateOpener",
    "DiscreteGateWithPedestrianPosition",
]


def load_merged_reference_metadata() -> dict:
    """Load and merge referenceMetadata from all server JSON files.

    Returns merged metadata with deduplicated lists and union of all values.
    """
    merged: dict = {
        "protocolTypes": [],
        "uiClasses": set(),
        "uiWidgets": set(),
        "uiClassifiers": set(),
        "uiProfiles": {},
    }
    seen_prefixes: set[str] = set()

    for server_file in sorted(SERVERS_DIR.glob("*.json")):
        data = json.loads(server_file.read_text(encoding="utf-8"))
        ref = data.get("referenceMetadata", {})

        for proto in ref.get("protocolTypes", []):
            if proto["prefix"] not in seen_prefixes:
                merged["protocolTypes"].append(proto)
                seen_prefixes.add(proto["prefix"])

        merged["uiClasses"].update(ref.get("uiClasses", []))
        merged["uiWidgets"].update(ref.get("uiWidgets", []))
        merged["uiClassifiers"].update(ref.get("uiClassifiers", []))

        for name, profile in ref.get("uiProfiles", {}).items():
            if name not in merged["uiProfiles"] or (
                profile is not None and merged["uiProfiles"][name] is None
            ):
                merged["uiProfiles"][name] = profile

    _merge_ui_data_from_fixtures(merged)

    return merged


def _merge_ui_data_from_fixtures(merged: dict) -> None:
    """Merge UI classes, widgets, classifiers and profiles from setup fixtures.

    Server reference metadata is the primary source, but the setup fixtures in
    tests/fixtures/setup/ occasionally reference UI values (especially profiles)
    that the reference endpoints of the servers we have access to do not expose.
    Profiles found only in fixtures are added without details (None), matching
    how unfetchable profiles are represented.
    """
    for fixture_file in FIXTURES_DIR.glob("*.json"):
        try:
            data = json.loads(fixture_file.read_text())
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
        for device in data.get("devices", []):
            definition = device.get("definition", {})
            for ui_class in (device.get("uiClass"), definition.get("uiClass")):
                if ui_class:
                    merged["uiClasses"].add(ui_class)
            for widget in (device.get("widget"), definition.get("widgetName")):
                if widget:
                    merged["uiWidgets"].add(widget)
            for source in (device, definition):
                for classifier in source.get("uiClassifiers", []) or []:
                    merged["uiClassifiers"].add(classifier)
            for profile_name in definition.get("uiProfiles", []) or []:
                merged["uiProfiles"].setdefault(profile_name, None)


def to_enum_name(value: str) -> str:
    """Convert camelCase to SCREAMING_SNAKE_CASE for enum names."""
    name = value.replace("ZWave", "ZWAVE_")
    name = name.replace("OTherm", "OTHERM_")
    name = name.replace("IPv4", "IPV4_")
    name = name.replace("IPv6", "IPV6_")
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    # Split before digit+uppercase sequences (e.g. "Gate4T" -> "Gate_4T")
    name = re.sub(r"([a-z])(\d+[A-Z]+)(?=[A-Z][a-z]|$)", r"\1_\2", name)
    name = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
    name = re.sub(r"(\d)([A-Z][a-z])", r"\1_\2", name)
    name = name.replace("APCDHW", "APC_DHW")
    name = re.sub(r"__+", "_", name)
    name = name.rstrip("_")
    return name.upper()


def command_to_enum_name(command_name: str) -> str:
    """Convert a command name (camelCase) to SCREAMING_SNAKE_CASE."""
    name = command_name.replace("/", "_")
    name = name.replace("-", "_")
    name = name.replace(" ", "_")
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    name = re.sub(r"([a-z])(\d)", r"\1_\2", name)
    name = re.sub(r"(\d)([A-Z])", r"\1_\2", name)
    name = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
    name = re.sub(r"__+", "_", name)
    name = name.strip("_")
    return name.upper()


# ---------------------------------------------------------------------------
# Protocol enum
# ---------------------------------------------------------------------------


def generate_protocol_enum(metadata: dict) -> None:
    """Generate the Protocol enum from merged metadata."""
    protocol_types = metadata["protocolTypes"]

    protocols: list[tuple[str, str, int | None, str | None]] = [
        (p["name"], p["prefix"], p.get("id"), p.get("label")) for p in protocol_types
    ]

    fetched_prefixes = {p["prefix"] for p in protocol_types}
    for name, prefix, proto_id, proto_label in ADDITIONAL_PROTOCOLS:
        if prefix not in fetched_prefixes:
            protocols.append((name, prefix, proto_id, proto_label))

    protocols.sort(key=lambda p: p[0])

    lines = [
        '"""Protocol enums describe device URL schemes used by Overkiz.',
        "",
        "THIS FILE IS AUTO-GENERATED. DO NOT EDIT MANUALLY.",
        "Run `uv run utils/generate_enums.py` to regenerate.",
        '"""',
        "",
        "from enum import StrEnum, unique",
        "",
        "from pyoverkiz.enums.base import UnknownEnumMixin",
        "",
        "",
        "@unique",
        "class Protocol(UnknownEnumMixin, StrEnum):",
        '    """Protocol used by Overkiz.',
        "",
        "    Values have been retrieved from /reference/protocolTypes",
        '    """',
        "",
        '    UNKNOWN = "unknown"',
        "",
    ]

    for name, prefix, protocol_id, label in protocols:
        if protocol_id is not None:
            lines.append(f'    {name} = "{prefix}"  # {protocol_id}: {label}')
        else:
            lines.append(f'    {name} = "{prefix}"')

    lines.append("")

    output_path = ENUMS_DIR / "protocol.py"
    output_path.write_text("\n".join(lines))
    print(f"✓ Generated {output_path} ({len(protocols)} protocols)")


# ---------------------------------------------------------------------------
# UI enums (classes, widgets, classifiers)
# ---------------------------------------------------------------------------


def generate_ui_enums(metadata: dict) -> None:
    """Generate UIClass, UIWidget, and UIClassifier enums."""
    ui_classes = sorted(metadata["uiClasses"])
    ui_widgets = sorted(metadata["uiWidgets"])
    ui_classifiers = sorted(metadata["uiClassifiers"])

    # Add hardcoded widgets not found across any server
    fetched_widget_values = set(ui_widgets)
    for widget_value in ADDITIONAL_WIDGETS:
        if widget_value not in fetched_widget_values:
            ui_widgets.append(widget_value)
    ui_widgets = sorted(ui_widgets)

    lines = [
        '"""UI enums for classes and widgets used to interpret device UI metadata.',
        "",
        "THIS FILE IS AUTO-GENERATED. DO NOT EDIT MANUALLY.",
        "Run `uv run utils/generate_enums.py` to regenerate.",
        '"""',
        "",
        "# ruff: noqa: S105",
        '# Enum values contain "PASS" in API names (e.g. PassAPC), not passwords',
        "",
        "from enum import StrEnum, unique",
        "",
        "from pyoverkiz.enums.base import UnknownEnumMixin",
        "",
        "",
        "@unique",
        "class UIClass(UnknownEnumMixin, StrEnum):",
        '    """Enumeration of UI classes used to describe device categories and behaviors."""',
        "",
        '    UNKNOWN = "Unknown"',
        "",
    ]

    for ui_class in ui_classes:
        enum_name = to_enum_name(ui_class)
        lines.append(f'    {enum_name} = "{ui_class}"')

    lines.append("")
    lines.append("")
    lines.append("@unique")
    lines.append("class UIWidget(UnknownEnumMixin, StrEnum):")
    lines.append(
        '    """Enumeration of UI widgets used by Overkiz for device presentation."""'
    )
    lines.append("")
    lines.append('    UNKNOWN = "Unknown"')
    lines.append("")

    for ui_widget in ui_widgets:
        enum_name = to_enum_name(ui_widget)
        lines.append(f'    {enum_name} = "{ui_widget}"')

    lines.append("")
    lines.append("")
    lines.append("@unique")
    lines.append("class UIClassifier(UnknownEnumMixin, StrEnum):")
    lines.append(
        '    """Enumeration of UI classifiers used to categorize device types."""'
    )
    lines.append("")
    lines.append('    UNKNOWN = "unknown"')
    lines.append("")

    for ui_classifier in ui_classifiers:
        enum_name = to_enum_name(ui_classifier)
        lines.append(f'    {enum_name} = "{ui_classifier}"')

    lines.append("")

    output_path = ENUMS_DIR / "ui.py"
    output_path.write_text("\n".join(lines))

    additional_widget_count = len(
        [w for w in ADDITIONAL_WIDGETS if w not in fetched_widget_values]
    )
    print(
        f"✓ Generated {output_path} "
        f"({len(ui_classes)} classes, {len(ui_widgets)} widgets, "
        f"{len(ui_classifiers)} classifiers, "
        f"+{additional_widget_count} hardcoded widgets)"
    )


# ---------------------------------------------------------------------------
# UI Profiles enum + docs
# ---------------------------------------------------------------------------


def _format_value_prototype_comment(vp: dict) -> str:
    """Format a value prototype dict into a readable string for comments."""
    type_str = vp.get("type", "").lower()
    parts = [type_str]

    min_val = vp.get("minValue")
    max_val = vp.get("maxValue")
    if min_val is not None and max_val is not None:
        parts.append(f"{min_val}-{max_val}")
    elif min_val is not None:
        parts.append(f">= {min_val}")
    elif max_val is not None:
        parts.append(f"<= {max_val}")

    if vp.get("enumValues"):
        enum_vals = ", ".join(f"'{v}'" for v in vp["enumValues"])
        parts.append(f"values: {enum_vals}")

    return " ".join(parts)


def _format_value_prototype_docs(vp: dict) -> str:
    """Format a value prototype dict for markdown docs."""
    type_str = f"`{vp.get('type', '').lower()}`"
    min_val = vp.get("minValue")
    max_val = vp.get("maxValue")
    if min_val is not None and max_val is not None:
        type_str += f" ({min_val}\N{EN DASH}{max_val})"
    elif min_val is not None:
        type_str += f" (≥ {min_val})"
    elif max_val is not None:
        type_str += f" (≤ {max_val})"
    if vp.get("enumValues"):
        type_str += " — " + ", ".join(f"`{v}`" for v in vp["enumValues"])
    return type_str


def generate_ui_profiles(metadata: dict) -> None:
    """Generate the UIProfile enum and docs page from merged profiles."""
    ui_profiles = metadata["uiProfiles"]
    sorted_names = sorted(ui_profiles.keys())

    def to_profile_enum_name(value: str) -> str:
        name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
        name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
        name = re.sub(r"__+", "_", name)
        return name.upper()

    # --- Enum file ---
    lines = [
        '"""UI Profile enums describe device capabilities through commands and states.',
        "",
        "THIS FILE IS AUTO-GENERATED. DO NOT EDIT MANUALLY.",
        "Run `uv run utils/generate_enums.py` to regenerate.",
        '"""',
        "",
        "from enum import StrEnum, unique",
        "",
        "from pyoverkiz.enums.base import UnknownEnumMixin",
        "",
        "",
        "@unique",
        "class UIProfile(UnknownEnumMixin, StrEnum):",
        '    """',
        "    UI Profiles define device capabilities through commands and states.",
        "",
        "    Each profile describes what a device can do (commands) and what information",
        "    it provides (states). Form factor indicates if the profile is tied to a",
        "    specific physical device type.",
        '    """',
        "",
        '    UNKNOWN = "Unknown"',
        "",
    ]

    for profile_name in sorted_names:
        details = ui_profiles[profile_name]
        enum_name = to_profile_enum_name(profile_name)

        if details is None:
            lines.append(f"    # {profile_name} (details unavailable)")
            lines.append(f'    {enum_name} = "{profile_name}"')
            lines.append("")
            continue

        comment_lines = []

        if details.get("commands"):
            comment_lines.append("Commands:")
            for cmd in details["commands"]:
                cmd_name = cmd["name"]
                desc = " ".join((cmd.get("description") or "").split()).strip()
                if cmd.get("parameters"):
                    param_strs = [
                        _format_value_prototype_comment(param["valuePrototypes"][0])
                        for param in cmd["parameters"]
                        if param.get("valuePrototypes")
                    ]
                    param_info = f"({', '.join(param_strs)})" if param_strs else "()"
                else:
                    param_info = "()"
                if desc:
                    comment_lines.append(f"  - {cmd_name}{param_info}: {desc}")
                else:
                    comment_lines.append(f"  - {cmd_name}{param_info}")

        if details.get("states"):
            if comment_lines:
                comment_lines.append("")
            comment_lines.append("States:")
            for state in details["states"]:
                state_name = state["name"]
                desc = " ".join((state.get("description") or "").split()).strip()
                if state.get("valuePrototypes"):
                    type_info = f" ({_format_value_prototype_comment(state['valuePrototypes'][0])})"
                else:
                    type_info = ""
                if desc:
                    comment_lines.append(f"  - {state_name}{type_info}: {desc}")
                else:
                    comment_lines.append(f"  - {state_name}{type_info}")

        if details.get("formFactor"):
            if comment_lines:
                comment_lines.append("")
            comment_lines.append("Form factor specific: Yes")

        if comment_lines:
            lines.append("    #")
            lines.append(f"    # {profile_name}")
            lines.append("    #")
            for comment_line in comment_lines:
                if comment_line:
                    lines.append(f"    # {comment_line}")
                else:
                    lines.append("    #")
        else:
            lines.append(f"    # {profile_name}")

        lines.append(f'    {enum_name} = "{profile_name}"')
        lines.append("")

    output_path = ENUMS_DIR / "ui_profile.py"
    output_path.write_text("\n".join(lines))

    found = sum(1 for v in ui_profiles.values() if v is not None)
    print(
        f"✓ Generated {output_path} ({found}/{len(ui_profiles)} profiles with details)"
    )

    # --- Docs page ---
    _generate_ui_profiles_docs(sorted_names, ui_profiles)


def _generate_ui_profiles_docs(
    sorted_names: list[str], ui_profiles: dict[str, dict | None]
) -> None:
    """Generate the ui-profiles.md documentation page."""
    lines = [
        "---",
        "hide:",
        "  - toc",
        "---",
        "",
        "# UI Profiles",
        "",
        "UI profiles describe device capabilities through the commands they accept "
        "and the states they expose. Each device has one or more profiles that define "
        "what it can do.",
        "",
        "!!! note",
        "    This page is auto-generated. Run `uv run utils/generate_enums.py` to regenerate.",
        "",
        f"**{len(sorted_names)} profiles** documented below.",
        "",
    ]

    for profile_name in sorted_names:
        details = ui_profiles[profile_name]
        lines.append(f"## {profile_name}")
        lines.append("")

        if details is None:
            lines.append("*Details unavailable.*")
            lines.append("")
            continue

        if details.get("formFactor"):
            lines.append(
                "*Form factor specific* — tied to a specific physical device type."
            )
            lines.append("")

        if details.get("commands"):
            lines.append("### Commands")
            lines.append("")
            lines.append("| Command | Parameters | Description |")
            lines.append("|---------|-----------|-------------|")
            for cmd in details["commands"]:
                params = ""
                if cmd.get("parameters"):
                    param_parts = []
                    for param in cmd["parameters"]:
                        if param.get("valuePrototypes"):
                            param_parts.append(
                                _format_value_prototype_docs(
                                    param["valuePrototypes"][0]
                                )
                            )
                        else:
                            param_parts.append("—")
                    params = ", ".join(param_parts)
                desc = (
                    (cmd.get("description") or "")
                    .replace("\n", " ")
                    .replace("|", "\\|")
                    .strip()
                )
                lines.append(f"| `{cmd['name']}` | {params} | {desc} |")
            lines.append("")

        if details.get("states"):
            lines.append("### States")
            lines.append("")
            lines.append("| State | Type | Description |")
            lines.append("|-------|------|-------------|")
            for state in details["states"]:
                type_info = ""
                if state.get("valuePrototypes"):
                    type_info = _format_value_prototype_docs(
                        state["valuePrototypes"][0]
                    )
                desc = (
                    (state.get("description") or "")
                    .replace("\n", " ")
                    .replace("|", "\\|")
                    .strip()
                )
                lines.append(f"| `{state['name']}` | {type_info} | {desc} |")
            lines.append("")

    output_path = DOCS_DIR / "ui-profiles.md"
    output_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"✓ Generated {output_path}")


# ---------------------------------------------------------------------------
# State + Attribute enums
# ---------------------------------------------------------------------------


def extract_states_from_fixtures(fixtures_dir: Path) -> set[str]:
    """Extract all qualified state names from fixture files."""
    states: set[str] = set()

    for fixture_file in fixtures_dir.glob("*.json"):
        try:
            data = json.loads(fixture_file.read_text())
            if "devices" not in data:
                continue
            for device in data["devices"]:
                definition = device.get("definition", {})
                for state in definition.get("states", []):
                    if "qualifiedName" in state:
                        states.add(state["qualifiedName"])
                    elif "name" in state:
                        states.add(state["name"])
        except (json.JSONDecodeError, KeyError, TypeError):
            continue

    return states


def extract_attributes_from_fixtures(fixtures_dir: Path) -> set[str]:
    """Extract all qualified attribute names from fixture files."""
    attributes: set[str] = set()

    for fixture_file in fixtures_dir.glob("*.json"):
        try:
            data = json.loads(fixture_file.read_text())
            if "devices" not in data:
                continue
            for device in data["devices"]:
                for attr in device.get("attributes", []):
                    if "name" in attr:
                        attributes.add(attr["name"])
        except (json.JSONDecodeError, KeyError, TypeError):
            continue

    return attributes


def extract_states_from_servers(servers_dir: Path) -> set[str]:
    """Extract qualified state names from per-server JSON files."""
    states: set[str] = set()

    if not servers_dir.exists():
        return states

    for server_file in servers_dir.glob("*.json"):
        try:
            data = json.loads(server_file.read_text())
            # Map protocol name (e.g. HLRR_WIFI) to its qualified-name prefix
            # (e.g. hlrrwifi); they differ for some protocols.
            prefixes = {
                p["name"]: p["prefix"]
                for p in data.get("referenceMetadata", {}).get("protocolTypes", [])
            }
            # From protocols section (prefix:StateName)
            for protocol, device_types in data.get("protocols", {}).items():
                prefix = prefixes.get(protocol, protocol.lower())
                for dt in device_types:
                    for s in dt.get("states", []):
                        if "name" in s:
                            states.add(f"{prefix}:{s['name']}")
            # From controllableDefinitions (has qualifiedName)
            for cd in data.get("controllableDefinitions", {}).values():
                for s in cd.get("states", []):
                    qn = s.get("qualifiedName")
                    if qn:
                        states.add(qn)
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    return states


def extract_attributes_from_servers(servers_dir: Path) -> set[str]:
    """Extract qualified attribute names from per-server JSON files."""
    attributes: set[str] = set()

    if not servers_dir.exists():
        return attributes

    for server_file in servers_dir.glob("*.json"):
        try:
            data = json.loads(server_file.read_text())
            for cd in data.get("controllableDefinitions", {}).values():
                for attr in cd.get("attributes", []):
                    qn = attr.get("qualifiedName")
                    if qn:
                        attributes.add(qn)
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    return attributes


def state_to_enum_name(qualified_name: str) -> str:
    """Convert a qualified state name like 'core:BatteryState' to CORE_BATTERY."""
    prefix, name = qualified_name.split(":", 1)
    name_stripped = name.removesuffix("State")
    return prefix.upper() + "_" + to_enum_name(name_stripped)


def attribute_to_enum_name(qualified_name: str) -> str:
    """Convert a qualified attribute name like 'core:FirmwareRevision' to CORE_FIRMWARE_REVISION."""
    prefix, name = qualified_name.split(":", 1)
    return prefix.upper() + "_" + to_enum_name(name)


def generate_state_enums() -> None:
    """Generate OverkizState and OverkizAttribute enums."""
    fixture_states = extract_states_from_fixtures(FIXTURES_DIR)
    catalog_states = extract_states_from_servers(SERVERS_DIR)
    fixture_attributes = extract_attributes_from_fixtures(FIXTURES_DIR)
    catalog_attributes = extract_attributes_from_servers(SERVERS_DIR)

    state_file = ENUMS_DIR / "state.py"
    content = state_file.read_text()

    existing_states = extract_enum_members(content, "OverkizState")
    existing_attributes = extract_enum_members(content, "OverkizAttribute")

    # Merge all state values
    all_state_values = set(existing_states.keys()) | fixture_states | catalog_states

    state_enum_names: set[str] = set()
    state_tuples: list[tuple[str, str]] = []
    for state_value in sorted(all_state_values):
        if ":" not in state_value:
            continue
        if state_value in existing_states:
            enum_name = existing_states[state_value]
        else:
            enum_name = state_to_enum_name(state_value)
        if enum_name not in state_enum_names:
            state_tuples.append((enum_name, state_value))
            state_enum_names.add(enum_name)

    state_tuples.sort(key=lambda x: x[0])

    # Merge all attribute values
    all_attribute_values = (
        set(existing_attributes.keys()) | fixture_attributes | catalog_attributes
    )

    attribute_enum_names: set[str] = set()
    attribute_tuples: list[tuple[str, str]] = []
    for attr_value in sorted(all_attribute_values):
        if ":" not in attr_value:
            continue
        if attr_value in existing_attributes:
            enum_name = existing_attributes[attr_value]
        else:
            enum_name = attribute_to_enum_name(attr_value)
        if enum_name not in attribute_enum_names:
            attribute_tuples.append((enum_name, attr_value))
            attribute_enum_names.add(enum_name)

    attribute_tuples.sort(key=lambda x: x[0])

    # Generate file
    lines = [
        '"""State and attribute enums describing Overkiz device states and attributes."""',
        "",
        "# ruff: noqa: S105",
        '# Enum values contain "PASS" or "TOKEN" in API names, not passwords',
        "",
        "from enum import StrEnum, unique",
        "",
        "",
        "@unique",
        "class OverkizAttribute(StrEnum):",
        '    """Device attributes used by Overkiz."""',
        "",
    ]

    for enum_name, attr_value in attribute_tuples:
        lines.append(f'    {enum_name} = "{attr_value}"')

    lines.append("")
    lines.append("")
    lines.append("@unique")
    lines.append("class OverkizState(StrEnum):")
    lines.append('    """Device states used by Overkiz."""')
    lines.append("")

    for enum_name, state_value in state_tuples:
        lines.append(f'    {enum_name} = "{state_value}"')

    lines.append("")

    state_file.write_text("\n".join(lines))

    new_states = len(all_state_values - set(existing_states.keys()))
    new_attrs = len(all_attribute_values - set(existing_attributes.keys()))
    print(
        f"✓ Generated {state_file} "
        f"({len(state_tuples)} states [+{new_states} new], "
        f"{len(attribute_tuples)} attributes [+{new_attrs} new])"
    )


# ---------------------------------------------------------------------------
# Command + CommandParam enums
# ---------------------------------------------------------------------------


def extract_commands_from_fixtures(fixtures_dir: Path) -> set[str]:
    """Extract all commands from fixture files."""
    commands: set[str] = set()

    for fixture_file in fixtures_dir.glob("*.json"):
        try:
            data = json.loads(fixture_file.read_text())
            if "devices" not in data:
                continue
            for device in data["devices"]:
                definition = device.get("definition", {})
                for command in definition.get("commands", []):
                    if "commandName" in command:
                        commands.add(command["commandName"])
        except (json.JSONDecodeError, KeyError, TypeError):
            continue

    return commands


def extract_state_values_from_fixtures(fixtures_dir: Path) -> set[str]:
    """Extract discrete state enum values from fixture files."""
    values: set[str] = set()

    for fixture_file in fixtures_dir.glob("*.json"):
        try:
            data = json.loads(fixture_file.read_text())
            if "devices" not in data:
                continue
            for device in data["devices"]:
                definition = device.get("definition", {})
                for state in definition.get("states", []):
                    if state.get("type") == "DiscreteState" and "values" in state:
                        for value in state["values"]:
                            if isinstance(value, str):
                                values.add(value)
        except (json.JSONDecodeError, KeyError, TypeError):
            continue

    return values


def extract_commands_from_servers(servers_dir: Path) -> set[str]:
    """Extract all command names from per-server JSON files."""
    commands: set[str] = set()

    if not servers_dir.exists():
        return commands

    for server_file in servers_dir.glob("*.json"):
        try:
            data = json.loads(server_file.read_text())
            for device_types in data.get("protocols", {}).values():
                for dt in device_types:
                    for cmd in dt.get("commands", []):
                        if "commandName" in cmd:
                            commands.add(cmd["commandName"])
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    return commands


def extract_state_values_from_servers(servers_dir: Path) -> set[str]:
    """Extract discrete state and command parameter enum values from per-server JSON.

    Pulls values from three places:
      - ``protocols.*.states[].valuePrototypes[].enumValues``
      - ``protocols.*.commands[].parameters[].valuePrototypes[].enumValues``
      - ``controllableDefinitions.*.states[].values`` (DiscreteState values)
    """
    values: set[str] = set()

    if not servers_dir.exists():
        return values

    for server_file in servers_dir.glob("*.json"):
        try:
            data = json.loads(server_file.read_text())
            for device_types in data.get("protocols", {}).values():
                for dt in device_types:
                    for state in dt.get("states", []):
                        for vp in state.get("valuePrototypes", []):
                            for ev in vp.get("enumValues", []):
                                if isinstance(ev, str):
                                    values.add(ev)
                    for command in dt.get("commands", []):
                        for param in command.get("parameters", []):
                            for vp in param.get("valuePrototypes", []):
                                for ev in vp.get("enumValues", []):
                                    if isinstance(ev, str):
                                        values.add(ev)
            for cd in data.get("controllableDefinitions", {}).values():
                for state in cd.get("states", []):
                    if state.get("type") == "DiscreteState":
                        for value in state.get("values", []):
                            if isinstance(value, str):
                                values.add(value)
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    return values


def extract_enum_members(content: str, class_name: str) -> dict[str, str]:
    """Extract enum member names keyed by their string value from a class definition."""
    module = ast.parse(content)

    for node in module.body:
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue

        members: dict[str, str] = {}
        for statement in node.body:
            if not isinstance(statement, ast.Assign):
                continue
            if len(statement.targets) != 1:
                continue

            target = statement.targets[0]
            if not isinstance(target, ast.Name):
                continue
            if not isinstance(statement.value, ast.Constant):
                continue
            if not isinstance(statement.value.value, str):
                continue

            members[statement.value.value] = target.id

        return members

    raise ValueError(f"Could not find enum class {class_name}")


def generate_command_enums() -> None:
    """Generate OverkizCommand and OverkizCommandParam enums."""
    fixture_commands = extract_commands_from_fixtures(FIXTURES_DIR)
    fixture_state_values = extract_state_values_from_fixtures(FIXTURES_DIR)
    catalog_commands = extract_commands_from_servers(SERVERS_DIR)
    catalog_state_values = extract_state_values_from_servers(SERVERS_DIR)

    command_file = ENUMS_DIR / "command.py"
    content = command_file.read_text()

    existing_commands = extract_enum_members(content, "OverkizCommand")
    existing_params = extract_enum_members(content, "OverkizCommandParam")

    # Merge all command values
    all_command_values = (
        set(existing_commands.keys()) | fixture_commands | catalog_commands
    )

    command_enum_names: set[str] = set()
    command_tuples: list[tuple[str, str]] = []
    for cmd_value in sorted(all_command_values):
        if cmd_value in existing_commands:
            enum_name = existing_commands[cmd_value]
        else:
            enum_name = command_to_enum_name(cmd_value)
        if enum_name not in command_enum_names:
            command_tuples.append((enum_name, cmd_value))
            command_enum_names.add(enum_name)

    command_tuples.sort(key=lambda x: x[0])

    # Merge all param values
    all_param_values = (
        set(existing_params.keys()) | fixture_state_values | catalog_state_values
    )

    param_enum_names: set[str] = set()
    param_tuples: list[tuple[str, str]] = []
    skipped_params: list[str] = []
    for param_value in sorted(all_param_values):
        if param_value in existing_params:
            enum_name = existing_params[param_value]
        else:
            enum_name = command_to_enum_name(param_value)
        # Some discrete values are purely numeric (e.g. "1", "2") and cannot
        # become valid Python identifiers — skip them rather than emit broken code.
        if not enum_name.isidentifier():
            skipped_params.append(param_value)
            continue
        if enum_name not in param_enum_names:
            param_tuples.append((enum_name, param_value))
            param_enum_names.add(enum_name)

    param_tuples.sort(key=lambda x: x[0])

    # Generate file
    lines = [
        '"""Command-related enums and parameters used by device commands."""',
        "",
        "# ruff: noqa: S105, RUF001",
        '# Enum values contain "PASS" in API names (e.g. PassAPC), not passwords,',
        "# and some are verbatim API values with ambiguous (e.g. Cyrillic) characters.",
        "",
        "from enum import StrEnum, unique",
        "",
        "",
        "@unique",
        "class OverkizCommand(StrEnum):",
        '    """Device commands used by Overkiz."""',
        "",
    ]

    for enum_name, cmd_value in command_tuples:
        if " " in cmd_value:
            lines.append(f'    {enum_name} = "{cmd_value}"  # value with space')
        else:
            lines.append(f'    {enum_name} = "{cmd_value}"')

    lines.append("")
    lines.append("")
    lines.append("@unique")
    lines.append("class OverkizCommandParam(StrEnum):")
    lines.append('    """Parameter used by Overkiz commands and/or states."""')
    lines.append("")

    for enum_name, param_value in param_tuples:
        if " " in param_value:
            lines.append(f'    {enum_name} = "{param_value}"  # value with space')
        else:
            lines.append(f'    {enum_name} = "{param_value}"')

    lines.append("")
    lines.append("")

    # Preserve ExecutionMode class from existing file
    execution_mode_start = content.find("@unique\nclass ExecutionMode")
    if execution_mode_start != -1:
        lines.append(content[execution_mode_start:].rstrip())
    lines.append("")

    command_file.write_text("\n".join(lines))

    new_commands = len(all_command_values - set(existing_commands.keys()))
    emitted_param_values = {value for _, value in param_tuples}
    new_params = len(emitted_param_values - set(existing_params.keys()))
    print(
        f"✓ Generated {command_file} "
        f"({len(command_tuples)} commands [+{new_commands} new], "
        f"{len(param_tuples)} params [+{new_params} new])"
    )
    if skipped_params:
        print(
            f"  Skipped {len(skipped_params)} param value(s) without a valid "
            f"identifier: {', '.join(repr(v) for v in sorted(skipped_params))}"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def format_generated_files() -> None:
    """Run ruff fixes and formatting on all generated enum files."""
    generated_files = [
        str(ENUMS_DIR / "protocol.py"),
        str(ENUMS_DIR / "ui.py"),
        str(ENUMS_DIR / "ui_profile.py"),
        str(ENUMS_DIR / "command.py"),
        str(ENUMS_DIR / "state.py"),
    ]
    subprocess.run(  # noqa: S603
        ["uv", "run", "ruff", "check", "--fix", *generated_files],  # noqa: S607
        check=True,
    )
    subprocess.run(  # noqa: S603
        ["uv", "run", "ruff", "format", *generated_files],  # noqa: S607
        check=True,
    )
    print("✓ Formatted generated files with ruff")


def generate_all() -> None:
    """Generate all enums from stored server data."""
    if not SERVERS_DIR.exists() or not list(SERVERS_DIR.glob("*.json")):
        print("No server data found in docs/data/")
        print("Run `uv run utils/fetch_server_data.py` first.")
        raise SystemExit(1)

    servers = [f.stem for f in sorted(SERVERS_DIR.glob("*.json"))]
    print(f"Reading data from: {', '.join(servers)}")
    print()

    metadata = load_merged_reference_metadata()

    generate_protocol_enum(metadata)
    generate_ui_enums(metadata)
    generate_ui_profiles(metadata)
    print()
    generate_state_enums()
    generate_command_enums()
    print()
    format_generated_files()


if __name__ == "__main__":
    generate_all()
