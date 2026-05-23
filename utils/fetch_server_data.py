"""Fetch all reference data from an Overkiz server and save as JSON.

This is the single data-fetching script. It pulls all reference endpoints
from a server and saves the result to data/servers/<server>.json.

Other scripts (generate_enums.py, generate_device_catalog.py) read from these
JSON files to generate code and documentation offline.

Usage:
    OVERKIZ_USERNAME=... OVERKIZ_PASSWORD=... uv run utils/fetch_server_data.py
    OVERKIZ_USERNAME=... OVERKIZ_PASSWORD=... uv run utils/fetch_server_data.py --server atlantic_cozytouch
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
from pyoverkiz.exceptions import OverkizError
from pyoverkiz.models import (
    DeviceSearchResult,
    DeviceTypeDefinition,
    UIProfileDefinition,
    ValuePrototype,
)

REQUEST_DELAY = 0.5
MAX_RETRIES = 5
BACKOFF_BASE = 10

SERVERS_DIR = Path(__file__).parent.parent / "data" / "servers"


async def _retry(coro_factory, *, label: str = "request"):
    """Call coro_factory() with retry + exponential backoff on QUOTA_EXCEEDED.

    coro_factory is a zero-argument callable that returns an awaitable (so we
    can re-create the coroutine on each retry attempt).
    """
    for attempt in range(MAX_RETRIES):
        try:
            result = await coro_factory()
        except OverkizError as e:
            if "QUOTA_EXCEEDED" in str(e):
                wait = BACKOFF_BASE * (2**attempt)
                print(f"  Rate limited on {label}, waiting {wait}s...")
                await asyncio.sleep(wait)
            else:
                raise
        else:
            await asyncio.sleep(REQUEST_DELAY)
            return result
    raise OverkizError(f"Gave up on {label} after {MAX_RETRIES} retries")


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


def _serialize_device_type(dt: DeviceTypeDefinition) -> dict:
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


def _serialize_ui_profile(profile: UIProfileDefinition) -> dict:
    """Serialize a UIProfileDefinition to a plain dict."""
    result: dict = {"name": profile.name, "formFactor": profile.form_factor}

    if profile.commands:
        result["commands"] = [
            {
                "name": cmd.name,
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
            }
            for cmd in profile.commands
        ]

    if profile.states:
        result["states"] = [
            {
                "name": state.name,
                **({"description": state.description} if state.description else {}),
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
            }
            for state in profile.states
        ]

    return result


async def fetch_server_data(server: Server) -> None:
    """Fetch all reference data from a server and save as JSON."""
    username = os.environ["OVERKIZ_USERNAME"]
    password = os.environ["OVERKIZ_PASSWORD"]

    async with OverkizClient(
        server=server,
        credentials=UsernamePasswordCredentials(username, password),
    ) as client:
        await client.login()

        # --- Reference metadata ---
        print("Fetching reference metadata...")

        controllable_types = await _retry(
            client.get_reference_controllable_types, label="controllableTypes"
        )
        print(f"  Controllable types: {len(controllable_types)}")

        ui_classes = await _retry(client.get_reference_ui_classes, label="ui/classes")
        ui_widgets = await _retry(client.get_reference_ui_widgets, label="ui/widgets")
        ui_classifiers = await _retry(
            client.get_reference_ui_classifiers, label="ui/classifiers"
        )
        print(
            f"  UI classes: {len(ui_classes)}, "
            f"widgets: {len(ui_widgets)}, "
            f"classifiers: {len(ui_classifiers)}"
        )

        protocol_types = await _retry(
            client.get_reference_protocol_types, label="protocolTypes"
        )
        print(f"  Protocols: {len(protocol_types)}")

        # --- UI Profiles ---
        print("\nFetching UI profiles...")
        ui_profile_names = await _retry(
            client.get_reference_ui_profile_names, label="ui/profileNames"
        )
        print(f"  Found {len(ui_profile_names)} profile names")

        ui_profiles: dict[str, dict | None] = {}
        for profile_name in sorted(ui_profile_names):
            try:
                details = await _retry(
                    lambda name=profile_name: client.get_reference_ui_profile(name),
                    label=f"profile/{profile_name}",
                )
                ui_profiles[profile_name] = _serialize_ui_profile(details)
            except OverkizError:
                ui_profiles[profile_name] = None

        found = sum(1 for v in ui_profiles.values() if v is not None)
        print(f"  Fetched {found}/{len(ui_profiles)} profiles with details")

        # --- Device types per protocol ---
        print("\nFetching device types per protocol...")
        all_device_types: dict[str, list[dict]] = {}
        total_count = 0

        for proto in protocol_types:
            print(f"  {proto.name} ({proto.prefix})...", end=" ")

            payload = {
                "protocolTypes": [proto.name],
                "withCommands": True,
                "withStates": True,
                "withAttributes": True,
                "withManufacturerReferences": True,
            }

            result: DeviceSearchResult = await _retry(
                lambda p=payload: client.search_reference_devices(p),
                label=f"devices/search/{proto.name}",
            )
            device_count = len(result.devices_types)
            total_count += device_count

            if not result.all_result:
                print(f"{device_count} types (TRUNCATED!)")
            else:
                print(f"{device_count} types")

            if result.devices_types:
                all_device_types[proto.name] = [
                    _serialize_device_type(dt) for dt in result.devices_types
                ]

        print(f"  Total: {total_count} device types")

        # --- Controllable definitions ---
        all_controllable_names: set[str] = set()
        for proto_devices in all_device_types.values():
            for d in proto_devices:
                name = d.get("controllableName")
                if name:
                    all_controllable_names.add(name)

        # Add names from user's setup (may not be available on all servers)
        try:
            controllables = await client.get_device_controllables()
            all_controllable_names.update(controllables.keys())
        except Exception as e:
            print(f"  Could not fetch setup controllables: {e}")

        try:
            devices = await client.get_devices()
            for device in devices:
                all_controllable_names.add(device.controllable_name)
        except Exception as e:
            print(f"  Could not fetch setup devices: {e}")

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
                definition = await _retry(
                    lambda n=name: client.get_reference_controllable(n),
                    label=f"controllable/{name}",
                )
                definitions_data[name] = definition
            except OverkizError:
                not_found.append(name)
            except Exception:
                not_found.append(name)

        print(f"  Done — found: {len(definitions_data)}, not found: {len(not_found)}")

    # --- Write output ---
    SERVERS_DIR.mkdir(parents=True, exist_ok=True)

    server_data = {
        "server": server.value,
        "referenceMetadata": {
            "controllableTypes": controllable_types,
            "protocolTypes": [
                {"id": p.id, "prefix": p.prefix, "name": p.name, "label": p.label}
                for p in protocol_types
            ],
            "uiClasses": ui_classes,
            "uiWidgets": ui_widgets,
            "uiClassifiers": ui_classifiers,
            "uiProfiles": ui_profiles,
        },
        "protocols": all_device_types,
        "controllableDefinitions": definitions_data,
    }

    server_path = SERVERS_DIR / f"{server.value}.json"
    server_path.write_text(
        json.dumps(server_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    size_mb = server_path.stat().st_size / 1024 / 1024
    print(f"\n✓ Written {server_path} ({size_mb:.1f} MB)")
    print(f"  {len(protocol_types)} protocols, {total_count} device types")
    print(f"  {len(definitions_data)} controllable definitions")
    print(f"  {found} UI profiles")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    server_choices = [s.value for s in Server]
    parser = argparse.ArgumentParser(
        description="Fetch all reference data from an Overkiz server."
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
    asyncio.run(fetch_server_data(Server(args.server)))
