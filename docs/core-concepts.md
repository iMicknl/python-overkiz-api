# Core concepts

## Servers and gateways

A server describes where the API calls go. A gateway is the physical hub in your home. Cloud servers route through vendor infrastructure; local servers talk directly to the gateway on your network.

## Setup and devices

The setup describes the current gateway configuration and device inventory. Devices expose metadata like `uiClass` and `widget`, plus a list of current `states`.

## Commands, actions, and action groups

The Overkiz API uses a three-level hierarchy to control devices:

- **Command** — A single instruction for a device, like `open`, `close`, or `setClosure(50)`. A command has a name and optional parameters.
- **Action** — One or more commands targeting a **single device** (identified by its device URL). The gateway allows at most one action per device in each action group.
- **Action group** — A batch of actions submitted to the gateway as a single execution. An action group can target multiple devices at once.

```
ActionGroup
├── Action (device A)
│   ├── Command("open")
│   └── Command("setClosure", [50])
└── Action (device B)
    └── Command("close")
```

Action groups come in two flavors:

- **Ad-hoc** — Built on the fly from `Action` and `Command` objects and executed via `execute_action_group()`.
- **Persisted** — Stored on the server (like saved scenes). Retrieved with `get_action_groups()` and executed by OID via `execute_persisted_action_group()`, or scheduled for a future timestamp via `schedule_persisted_action_group()`.

## Executions

When an action group is submitted, the server returns an `exec_id` identifying the **execution**. An execution tracks the lifecycle of a submitted action group — from queued, to running, to completed or failed.

- **Track** running executions with `get_current_executions()` or `get_current_execution(exec_id)`.
- **Cancel** a running execution with `cancel_execution(exec_id)`.
- **Review** past results with `get_execution_history()`.

Executions run asynchronously on the gateway. State changes are delivered through events, so you typically combine execution with an event listener to know when commands finish.

## Execution modes

An optional `ExecutionMode` can be passed when executing an action group:

- `HIGH_PRIORITY` — Bypasses the normal execution queue.
- `GEOLOCATED` — Triggered by geolocation rules.
- `INTERNAL` — Used for internal/system executions.

Execution modes are only supported by the **Cloud API**. The local API (Somfy TaHoma Developer Mode) does not accept an execution mode and will reject the request. See [Somfy-TaHoma-Developer-Mode#227](https://github.com/Somfy-Developer/Somfy-TaHoma-Developer-Mode/issues/227).

## UI profiles and classifiers

Each device definition includes **UI profiles** and **UI classifiers** that describe what the device can do at a higher level than raw commands.

- **UIProfile** — Describes a device capability in terms of commands and states. For example, `Closeable` means the device supports `setClosure` and `stop`, while `StatefulCloseable` adds a `core:ClosureState` state. A device can have multiple profiles (e.g. both `Closeable` and `Dimmable`).
- **UIClassifier** — Categorizes the device's role (e.g. `HEATING_SYSTEM`, `SENSOR`, `EMITTER`).

Profiles enable capability-based routing without checking individual command names:

```python
from pyoverkiz.enums import UIProfile, UIClassifier

if UIProfile.CLOSEABLE in device.definition.ui_profiles:
    # This device supports cover operations

if UIClassifier.HEATING_SYSTEM in device.definition.ui_classifiers:
    # This device is part of a heating system
```

This is more robust than matching on `ui_class` or `widget` strings, because profiles are standardized across device types and vendors. A device's profiles are auto-generated from the Overkiz server's `/reference/ui/profiles` endpoint.

## States

States are name/value pairs that represent the current device status, such as closure position or temperature.

## Events and listeners

The API uses an event listener that you register once per session. Fetching events drains the server-side buffer. Events include execution state changes, device state updates, and other notifications.

## Authentication strategies

The library supports multiple authentication methods depending on the server:

- **Username/Password**: Most cloud servers (Somfy, Cozytouch, Hitachi, Nexity)
- **Bearer Token**: Cloud servers with pre-issued tokens
- **Local Token**: Somfy Developer Mode (local gateways)
- **OAuth2 with PKCE**: Rexel (Azure AD B2C)

Each server automatically selects the appropriate authentication strategy based on the credentials provided.

Rexel supports two authentication modes:

- **Library-driven code exchange** (`RexelOAuthCodeCredentials`): pyoverkiz
  performs the PKCE code exchange and refreshes its own tokens. Best for
  standalone use.
- **Externally-managed token** (`RexelTokenCredentials`): the OAuth2 lifecycle
  is owned outside the library (e.g. Home Assistant's `application_credentials`
  platform). Supply an async `access_token_callback` or a static `access_token`.
  Best when a host application already manages OAuth.

Both Rexel modes support multiple gateways: after `login()`, call
`discover_gateways()` and `select_gateway()` to scope requests (a sole gateway
is auto-selected).

## Relationship diagram

```
Client
  │
  ├── Server (cloud or local)
  │
  └── Gateway
        │
        ├── Setup
        │     │
        │     └── Devices
        │           │
        │           ├── States (name/value pairs)
        │           └── Actions ──► Commands ──► Parameters
        │
        ├── Action Groups (persisted)
        │
        ├── Executions (running action groups)
        │
        └── Event Listener ──► Events
```
