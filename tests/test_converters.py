"""Tests for the cattrs converter module."""

from __future__ import annotations

from typing import Any

import humps

from pyoverkiz.converters import structure
from pyoverkiz.enums import (
    ExecutionState,
    GatewaySubType,
    GatewayType,
)
from pyoverkiz.models import (
    Connectivity,
    Device,
    Event,
    Gateway,
    HistoryExecution,
    Option,
    OptionParameter,
    Partner,
    Place,
    Setup,
    Zone,
    ZoneItem,
)


class TestEnumStructuring:
    """Tests for automatic enum conversion during structuring."""

    def test_gateway_enum_fields(self):
        """Gateway correctly structures GatewayType and GatewaySubType from ints."""
        gw = structure(
            {
                "gateway_id": "1234-5678-9012",
                "connectivity": {"status": "OK", "protocol_version": "2025.3"},
                "type": 15,
                "sub_type": 1,
            },
            Gateway,
        )
        assert gw.type == GatewayType.TAHOMA
        assert gw.sub_type == GatewaySubType.TAHOMA_BASIC

    def test_gateway_none_enum_fields(self):
        """Gateway handles None enum values gracefully."""
        gw = structure(
            {
                "gateway_id": "1234-5678-9012",
                "connectivity": {"status": "OK", "protocol_version": "2025.3"},
                "type": None,
                "sub_type": None,
            },
            Gateway,
        )
        assert gw.type is None
        assert gw.sub_type is None

    def test_history_execution_enum_fields(self):
        """HistoryExecution structures ExecutionState and related enums."""
        he = structure(
            {
                "id": "exec-1",
                "event_time": 1234567890,
                "owner": "test@test.com",
                "source": "api",
                "duration": 100,
                "type": "IMMEDIATE",
                "state": "COMPLETED",
                "failure_type": "NO_FAILURE",
                "commands": [],
                "execution_type": "IMMEDIATE_EXECUTION",
                "execution_sub_type": "ACTION_GROUP",
            },
            HistoryExecution,
        )
        assert he.state == ExecutionState.COMPLETED


class TestNestedModelStructuring:
    """Tests for nested model construction via the converter."""

    def test_gateway_nested_connectivity_and_partners(self):
        """Gateway auto-structures nested Connectivity and Partner models."""
        gw = structure(
            {
                "gateway_id": "1234-5678-9012",
                "connectivity": {"status": "OK", "protocol_version": "2025.3"},
                "partners": [
                    {
                        "activated": True,
                        "name": "Somfy",
                        "id": "p-1",
                        "status": "ACTIVE",
                    }
                ],
            },
            Gateway,
        )
        assert isinstance(gw.connectivity, Connectivity)
        assert gw.connectivity.protocol_version == "2025.3"
        assert len(gw.partners) == 1
        assert isinstance(gw.partners[0], Partner)

    def test_place_recursive_sub_places(self):
        """Place structures recursive sub_places."""
        place = structure(
            {
                "creation_time": 100,
                "label": "House",
                "type": 0,
                "oid": "place-1",
                "sub_places": [
                    {
                        "creation_time": 200,
                        "label": "Bedroom",
                        "type": 1,
                        "oid": "place-2",
                        "sub_places": [],
                    }
                ],
            },
            Place,
        )
        assert place.label == "House"
        assert place.id == "place-1"
        assert len(place.sub_places) == 1
        assert isinstance(place.sub_places[0], Place)
        assert place.sub_places[0].label == "Bedroom"
        assert place.sub_places[0].id == "place-2"

    def test_option_nested_parameters(self):
        """Option structures nested OptionParameter list."""
        opt = structure(
            {
                "creation_time": 100,
                "last_update_time": 200,
                "option_id": "opt-1",
                "start_date": 300,
                "parameters": [{"name": "key", "value": "val"}],
            },
            Option,
        )
        assert opt.option_id == "opt-1"
        assert len(opt.parameters) == 1
        assert isinstance(opt.parameters[0], OptionParameter)

    def test_zone_nested_items(self):
        """Zone structures nested ZoneItem list."""
        zone = structure(
            {
                "creation_time": 100,
                "last_update_time": 200,
                "label": "Living Room",
                "type": 1,
                "oid": "z-1",
                "items": [
                    {
                        "item_type": "device",
                        "device_oid": "d-1",
                        "device_url": "io://x/y",
                    }
                ],
            },
            Zone,
        )
        assert zone.label == "Living Room"
        assert len(zone.items) == 1
        assert isinstance(zone.items[0], ZoneItem)
        assert zone.items[0].item_type == "device"


class TestFieldAliasing:
    """Tests for models with __attrs_post_init__ aliasing."""

    def test_gateway_id_mirroring(self):
        """Gateway mirrors gateway_id into id."""
        gw = structure(
            {
                "gateway_id": "1234-5678-9012",
                "connectivity": {"status": "OK", "protocol_version": "2025.3"},
            },
            Gateway,
        )
        assert gw.gateway_id == "1234-5678-9012"
        assert gw.id == "1234-5678-9012"

    def test_place_oid_mirroring(self):
        """Place mirrors oid into id."""
        place = structure(
            {
                "creation_time": 100,
                "label": "House",
                "type": 0,
                "oid": "place-1",
                "sub_places": [],
            },
            Place,
        )
        assert place.oid == "place-1"
        assert place.id == "place-1"


class TestUnknownFields:
    """Tests for unknown field handling."""

    def test_unknown_fields_do_not_raise(self):
        """Unknown fields are discarded without raising (forbid_extra_keys=False)."""
        conn = structure(
            {
                "status": "OK",
                "protocol_version": "2025.3",
                "future_field": 42,
                "another_one": True,
            },
            Connectivity,
        )
        assert conn.status == "OK"


class TestSetupEndToEnd:
    """End-to-end test structuring a full decamelized Setup payload."""

    def test_setup_from_decamelized_response(self):
        """Setup structures the complete nested hierarchy from decamelized API data."""
        raw_setup: dict[str, Any] = humps.decamelize(
            {
                "id": "setup-123",
                "creationTime": 1000,
                "gateways": [
                    {
                        "gatewayId": "1234-5678-9012",
                        "connectivity": {
                            "status": "OK",
                            "protocolVersion": "2025.3.1",
                        },
                        "type": 15,
                        "partners": [],
                    }
                ],
                "devices": [
                    {
                        "deviceURL": "io://1234-5678-9012/10077486",
                        "label": "Shutter",
                        "controllableName": "io:RollerShutterGenericIOComponent",
                        "definition": {
                            "commands": [{"commandName": "close", "nparams": 0}],
                            "states": [],
                            "dataProperties": [],
                        },
                        "states": [],
                        "available": True,
                        "enabled": True,
                        "type": 1,
                    }
                ],
                "rootPlace": {
                    "creationTime": 100,
                    "label": "House",
                    "type": 0,
                    "oid": "place-1",
                    "subPlaces": [],
                },
            }
        )
        setup = structure(raw_setup, Setup)

        assert setup.id == "setup-123"
        assert len(setup.gateways) == 1
        assert isinstance(setup.gateways[0], Gateway)
        assert setup.gateways[0].type == GatewayType.TAHOMA
        assert len(setup.devices) == 1
        assert isinstance(setup.devices[0], Device)
        assert setup.root_place is not None
        assert isinstance(setup.root_place, Place)
        assert setup.root_place.label == "House"

    def test_event_with_state_casting(self):
        """Event structures device_states with EventState string-to-int casting."""
        raw = humps.decamelize(
            {
                "name": "DeviceStateChangedEvent",
                "timestamp": 1234567890,
                "deviceURL": "io://1234-5678-9012/10077486",
                "deviceStates": [
                    {"name": "core:ClosureState", "type": 1, "value": "75"},
                ],
            }
        )
        event = structure(raw, Event)
        assert event.device_url == "io://1234-5678-9012/10077486"
        assert len(event.device_states) == 1
        assert event.device_states[0].value == 75
        assert isinstance(event.device_states[0].value, int)
