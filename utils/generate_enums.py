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
            '    UNKNOWN = "unknown"',
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
        lines.append('    UNKNOWN = "unknown"')
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


async def generate_all() -> None:
    """Generate all enums from the Overkiz API."""
    await generate_protocol_enum()
    print()
    await generate_ui_enums()


asyncio.run(generate_all())
