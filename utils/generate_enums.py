"""Generate enum files from the Overkiz API reference data."""

# ruff: noqa: T201

from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path
from typing import cast

from pyoverkiz.auth.credentials import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import Server
from pyoverkiz.exceptions import OverkizException
from pyoverkiz.models import UIProfileDefinition, ValuePrototype

# Hardcoded protocols that may not be available on all servers
# Format: (name, prefix)
ADDITIONAL_PROTOCOLS = [
    ("HLRR_WIFI", "hlrrwifi"),
    ("MODBUSLINK", "modbuslink"),
    ("RTN", "rtn"),
]

# Hardcoded widgets that may not be available on all servers
# Format: (enum_name, value)
ADDITIONAL_WIDGETS = [
    ("ALARM_PANEL_CONTROLLER", "AlarmPanelController"),
    ("CYCLIC_GARAGE_DOOR", "CyclicGarageDoor"),
    ("CYCLIC_SWINGING_GATE_OPENER", "CyclicSwingingGateOpener "),
    ("DISCRETE_GATE_WITH_PEDESTRIAN_POSITION", "DiscreteGateWithPedestrianPosition"),
    ("HLRR_WIFI_BRIDGE", "HLRRWifiBridge"),
    ("NODE", "Node"),
]


async def generate_protocol_enum() -> None:
    """Generate the Protocol enum from the Overkiz API."""
    username = os.environ["OVERKIZ_USERNAME"]
    password = os.environ["OVERKIZ_PASSWORD"]

    async with OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials(username, password),
    ) as client:
        await client.login()

        protocol_types = await client.get_reference_protocol_types()

        # Build list of protocol entries (name, prefix, id, label)
        protocols: list[tuple[str, str, int | None, str | None]] = [
            (p.name, p.prefix, p.id, p.label) for p in protocol_types
        ]

        # Add hardcoded protocols that may not be on all servers (avoid duplicates)
        fetched_prefixes = {p.prefix for p in protocol_types}
        for name, prefix in ADDITIONAL_PROTOCOLS:
            if prefix not in fetched_prefixes:
                protocols.append((name, prefix, None, None))

        # Sort by name for consistent output
        protocols.sort(key=lambda p: p[0])

        # Generate the enum file content
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

        # Add each protocol as an enum value with label comment
        for name, prefix, protocol_id, label in protocols:
            if protocol_id is not None:
                lines.append(f'    {name} = "{prefix}"  # {protocol_id}: {label}')
            else:
                lines.append(f'    {name} = "{prefix}"')

        lines.append("")  # End with newline

        # Write to the protocol.py file
        output_path = (
            Path(__file__).parent.parent / "pyoverkiz" / "enums" / "protocol.py"
        )
        output_path.write_text("\n".join(lines))

        fetched_count = len(protocol_types)
        additional_count = len(
            [p for p in ADDITIONAL_PROTOCOLS if p[1] not in fetched_prefixes]
        )

        print(f"✓ Generated {output_path}")
        print(f"✓ Added {fetched_count} protocols from API")
        print(f"✓ Added {additional_count} additional hardcoded protocols")
        print(f"✓ Total: {len(protocols)} protocols")


async def generate_ui_enums() -> None:
    """Generate the UIClass and UIWidget enums from the Overkiz API."""
    username = os.environ["OVERKIZ_USERNAME"]
    password = os.environ["OVERKIZ_PASSWORD"]

    async with OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials(username, password),
    ) as client:
        await client.login()

        ui_classes = cast(list[str], await client.get_reference_ui_classes())
        ui_widgets = cast(list[str], await client.get_reference_ui_widgets())

        # Convert camelCase to SCREAMING_SNAKE_CASE for enum names
        def to_enum_name(value: str) -> str:
            # Handle special cases first
            name = value.replace("ZWave", "ZWAVE_")
            name = name.replace("OTherm", "OTHERM_")

            # Insert underscore before uppercase letters
            name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
            name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)

            # Fix specific cases after general conversion
            name = name.replace("APCDHW", "APC_DHW")

            # Clean up any double underscores and trailing underscores
            name = re.sub(r"__+", "_", name)
            name = name.rstrip("_")

            return name.upper()

        # Generate the enum file content
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

        # Add UI classes
        sorted_classes = sorted(ui_classes)
        for ui_class in sorted_classes:
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

        # Add UI widgets
        sorted_widgets = sorted(ui_widgets)

        # Add hardcoded widgets that may not be on all servers (avoid duplicates)
        fetched_widget_values = set(ui_widgets)
        for _enum_name, widget_value in ADDITIONAL_WIDGETS:
            if widget_value not in fetched_widget_values:
                sorted_widgets.append(widget_value)

        sorted_widgets = sorted(sorted_widgets)

        for ui_widget in sorted_widgets:
            enum_name = to_enum_name(ui_widget)
            lines.append(f'    {enum_name} = "{ui_widget}"')

        lines.append("")  # End with newline

        # Fetch and add UI classifiers
        ui_classifiers = cast(list[str], await client.get_reference_ui_classifiers())

        lines.append("")
        lines.append("@unique")
        lines.append("class UIClassifier(UnknownEnumMixin, StrEnum):")
        lines.append(
            '    """Enumeration of UI classifiers used to categorize device types."""'
        )
        lines.append("")
        lines.append('    UNKNOWN = "unknown"')
        lines.append("")

        # Add UI classifiers
        sorted_classifiers = sorted(ui_classifiers)
        for ui_classifier in sorted_classifiers:
            enum_name = to_enum_name(ui_classifier)
            lines.append(f'    {enum_name} = "{ui_classifier}"')

        lines.append("")  # End with newline

        # Write to the ui.py file
        output_path = Path(__file__).parent.parent / "pyoverkiz" / "enums" / "ui.py"
        output_path.write_text("\n".join(lines))

        additional_widget_count = len(
            [w for w in ADDITIONAL_WIDGETS if w[1] not in fetched_widget_values]
        )

        print(f"✓ Generated {output_path}")
        print(f"✓ Added {len(ui_classes)} UI classes")
        print(f"✓ Added {len(ui_widgets)} UI widgets from API")
        print(f"✓ Added {additional_widget_count} additional hardcoded UI widgets")
        print(f"✓ Total: {len(sorted_widgets)} UI widgets")
        print(f"✓ Added {len(sorted_classifiers)} UI classifiers")


async def generate_ui_profiles() -> None:
    """Generate the UIProfile enum from the Overkiz API."""
    username = os.environ["OVERKIZ_USERNAME"]
    password = os.environ["OVERKIZ_PASSWORD"]

    async with OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials(username, password),
    ) as client:
        await client.login()

        ui_profile_names = await client.get_reference_ui_profile_names()

        # Fetch details for all profiles
        profiles_with_details: list[tuple[str, UIProfileDefinition | None]] = []

        for profile_name in ui_profile_names:
            print(f"Fetching {profile_name}...")
            try:
                details = await client.get_reference_ui_profile(profile_name)
                profiles_with_details.append((profile_name, details))
            except OverkizException:
                print(f"  ! Could not fetch details for {profile_name}")
                profiles_with_details.append((profile_name, None))

        # Convert camelCase to SCREAMING_SNAKE_CASE for enum names
        def to_enum_name(value: str) -> str:
            # Insert underscore before uppercase letters
            name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
            name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)

            # Clean up any double underscores
            name = re.sub(r"__+", "_", name)

            return name.upper()

        def format_value_prototype(vp: ValuePrototype) -> str:
            """Format a value prototype into a readable string."""
            type_str = vp.type.lower()
            parts = [type_str]

            if vp.min_value is not None and vp.max_value is not None:
                parts.append(f"{vp.min_value}-{vp.max_value}")
            elif vp.min_value is not None:
                parts.append(f">= {vp.min_value}")
            elif vp.max_value is not None:
                parts.append(f"<= {vp.max_value}")

            if vp.enum_values:
                enum_vals = ", ".join(f"'{v}'" for v in vp.enum_values)
                parts.append(f"values: {enum_vals}")

            return " ".join(parts)

        def clean_description(desc: str) -> str:
            """Clean description text to fit in a single-line comment."""
            # Remove newlines and excessive whitespace
            cleaned = " ".join(desc.split())
            return cleaned.strip()

        # Generate the enum file content
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
            "    ",
            "    Each profile describes what a device can do (commands) and what information",
            "    it provides (states). Form factor indicates if the profile is tied to a",
            "    specific physical device type.",
            '    """',
            "",
            '    UNKNOWN = "Unknown"',
            "",
        ]

        # Sort profiles by name for consistent output
        profiles_with_details.sort(key=lambda p: p[0])

        # Add each profile with detailed comments
        for profile_name, details_obj in profiles_with_details:
            enum_name = to_enum_name(profile_name)

            if details_obj is None:
                # No details available
                lines.append(f"    # {profile_name} (details unavailable)")
                lines.append(f'    {enum_name} = "{profile_name}"')
                lines.append("")
                continue

            # Build multi-line comment
            comment_lines = []

            # Add commands if present
            if details_obj.commands:
                comment_lines.append("Commands:")
                for cmd in details_obj.commands:
                    cmd_name = cmd.name
                    desc = clean_description(cmd.description or "")

                    # Get parameter info
                    if cmd.prototype and cmd.prototype.parameters:
                        param_strs = []
                        for param in cmd.prototype.parameters:
                            if param.value_prototypes:
                                param_strs.append(
                                    format_value_prototype(param.value_prototypes[0])
                                )
                        param_info = (
                            f"({', '.join(param_strs)})" if param_strs else "()"
                        )
                    else:
                        param_info = "()"

                    if desc:
                        comment_lines.append(f"  - {cmd_name}{param_info}: {desc}")
                    else:
                        comment_lines.append(f"  - {cmd_name}{param_info}")

            # Add states if present
            if details_obj.states:
                if comment_lines:
                    comment_lines.append("")
                comment_lines.append("States:")
                for state in details_obj.states:
                    state_name = state.name
                    desc = clean_description(state.description or "")

                    # Get value prototype info
                    if state.prototype and state.prototype.value_prototypes:
                        type_info = f" ({format_value_prototype(state.prototype.value_prototypes[0])})"
                    else:
                        type_info = ""

                    if desc:
                        comment_lines.append(f"  - {state_name}{type_info}: {desc}")
                    else:
                        comment_lines.append(f"  - {state_name}{type_info}")

            # Add form factor info
            if details_obj.form_factor:
                if comment_lines:
                    comment_lines.append("")
                comment_lines.append("Form factor specific: Yes")

            # If we have any details, add the comment block
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
                # Simple single-line comment
                lines.append(f"    # {profile_name}")

            lines.append(f'    {enum_name} = "{profile_name}"')
            lines.append("")

        # Write to the ui_profile.py file
        output_path = (
            Path(__file__).parent.parent / "pyoverkiz" / "enums" / "ui_profile.py"
        )
        output_path.write_text("\n".join(lines))

        print(f"\n✓ Generated {output_path}")
        print(f"✓ Added {len(profiles_with_details)} UI profiles")
        print(
            f"✓ Profiles with details: {sum(1 for _, d in profiles_with_details if d is not None)}"
        )
        print(
            f"✓ Profiles without details: {sum(1 for _, d in profiles_with_details if d is None)}"
        )


async def generate_all() -> None:
    """Generate all enums from the Overkiz API."""
    await generate_protocol_enum()
    print()
    await generate_ui_enums()
    print()
    await generate_ui_profiles()


asyncio.run(generate_all())
