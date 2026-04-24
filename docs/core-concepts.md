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

## States

States are name/value pairs that represent the current device status, such as closure position or temperature.

## Events and listeners

The API uses an event listener that you register once per session. Fetching events drains the server-side buffer. Events include execution state changes, device state updates, and other notifications.

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
