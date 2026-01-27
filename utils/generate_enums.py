"""Generate enum files from the Overkiz API reference data."""

# ruff: noqa: T201

from __future__ import annotations

import asyncio
import os
from pathlib import Path

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


asyncio.run(generate_protocol_enum())
