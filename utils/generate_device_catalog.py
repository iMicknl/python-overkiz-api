"""Generate a device catalog by querying all protocols via /reference/devices/search.

Fetches full device type definitions for every protocol supported by the server,
including commands (with parameter prototypes), states, attributes and manufacturer
references. Outputs a JSON catalog and a summary text file.

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
from pyoverkiz.models import DeviceSearchResult, DeviceTypeDefinition

OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "device-catalog"


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
                                    {
                                        "type": vp.type,
                                        **(
                                            {"minValue": vp.min_value}
                                            if vp.min_value is not None
                                            else {}
                                        ),
                                        **(
                                            {"maxValue": vp.max_value}
                                            if vp.max_value is not None
                                            else {}
                                        ),
                                        **(
                                            {"enumValues": vp.enum_values}
                                            if vp.enum_values
                                            else {}
                                        ),
                                    }
                                    for vp in p.value_prototypes
                                ],
                            }
                            for p in cmd.prototype.parameters
                        ]
                    }
                    if cmd.prototype and cmd.prototype.parameters
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
                            {
                                "type": vp.type,
                                **(
                                    {"minValue": vp.min_value}
                                    if vp.min_value is not None
                                    else {}
                                ),
                                **(
                                    {"maxValue": vp.max_value}
                                    if vp.max_value is not None
                                    else {}
                                ),
                                **(
                                    {"enumValues": vp.enum_values}
                                    if vp.enum_values
                                    else {}
                                ),
                            }
                            for vp in state.prototype.value_prototypes
                        ]
                    }
                    if state.prototype and state.prototype.value_prototypes
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

        # Write output
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Full catalog JSON
        catalog_path = OUTPUT_DIR / "device_catalog.json"
        catalog_data = {
            "server": server.name,
            "totalDeviceTypes": total_count,
            "protocols": all_device_types,
        }
        catalog_path.write_text(
            json.dumps(catalog_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\n✓ Written catalog to {catalog_path}")

        print("\nFetching individual controllable definitions...")
        all_controllable_names: set[str] = set()

        # Get from reference/controllable for all devices in setup
        devices = await client.get_devices()
        for device in devices:
            all_controllable_names.add(device.controllable_name)

        # Add controllable names from setup mapping
        all_controllable_names.update(controllables.keys())

        names_path = OUTPUT_DIR / "controllable_names.txt"
        names_path.write_text(
            "\n".join(sorted(all_controllable_names)), encoding="utf-8"
        )
        print(
            f"✓ Written {len(all_controllable_names)} controllable names to {names_path}"
        )

        # Summary with command/state details per controllable
        print("\nFetching controllable definitions...")
        definitions_data: dict[str, dict] = {}

        for name in sorted(all_controllable_names):
            try:
                definition = await client.get_reference_controllable(name)
                definitions_data[name] = definition
            except Exception as e:
                print(f"  ! Could not fetch definition for {name}: {e}")

        definitions_path = OUTPUT_DIR / "controllable_definitions.json"
        definitions_path.write_text(
            json.dumps(definitions_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"✓ Written {len(definitions_data)} definitions to {definitions_path}")

        # Generate summary text
        summary_lines = [
            f"Device Catalog Summary — Server: {server.name}",
            f"{'=' * 60}",
            f"Total protocols: {len(protocol_types)}",
            f"Total device types (by protocol): {total_count}",
            f"Total device types (unfiltered): {len(result_all.devices_types)}",
            f"Controllable names in setup: {len(controllables)}",
            f"Unique controllable names: {len(all_controllable_names)}",
            "",
            "Protocols:",
        ]

        for proto in protocol_types:
            count = len(all_device_types.get(proto.name, []))
            summary_lines.append(
                f"  {proto.name} ({proto.prefix}): {count} device types"
            )

        summary_lines.extend(["", "Controllable Names:", ""])
        for name in sorted(all_controllable_names):
            defn = definitions_data.get(name, {})
            commands = defn.get("commands", [])
            states = defn.get("states", [])
            cmd_names = [c["commandName"] for c in commands] if commands else []
            state_names = (
                [s.get("qualifiedName", s.get("name", "?")) for s in states]
                if states
                else []
            )

            summary_lines.append(f"  {name}")
            if cmd_names:
                summary_lines.append(f"    Commands: {', '.join(cmd_names[:10])}")
                if len(cmd_names) > 10:
                    summary_lines.append(
                        f"              ... and {len(cmd_names) - 10} more"
                    )
            if state_names:
                summary_lines.append(f"    States: {', '.join(state_names[:10])}")
                if len(state_names) > 10:
                    summary_lines.append(
                        f"            ... and {len(state_names) - 10} more"
                    )

        summary_path = OUTPUT_DIR / "summary.txt"
        summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
        print(f"✓ Written summary to {summary_path}")


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
