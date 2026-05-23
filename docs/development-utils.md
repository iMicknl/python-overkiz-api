# Development Utilities

Scripts in the `utils/` directory help generate enum source files, documentation pages, and test fixtures from the Overkiz API.

## Architecture

```
utils/
├── fetch_server_data.py      # Fetches all reference data from a server
├── generate_enums.py         # Generates enum .py files (offline)
├── generate_device_catalog.py # Generates device-types.md docs (offline)
└── mask_fixtures.py          # Masks sensitive data in test fixtures
```

**Data flow:**

```
  Overkiz API
       │
       ▼
  fetch_server_data.py  ──►  docs/data/<server>.json
                                          │
                        ┌─────────────────┼─────────────────┐
                        ▼                 ▼                  ▼
              generate_enums.py   generate_device_catalog.py
                        │                 │
                        ▼                 ▼
              pyoverkiz/enums/*.py   docs/device-types.md
                                    docs/ui-profiles.md
```

The per-server JSON files in `docs/data/` are the single source of truth. They are checked into git and accumulate over time as you gain access to more servers.

## fetch_server_data.py

Fetches all reference data from a single Overkiz server and saves it as a JSON file.

```bash
OVERKIZ_USERNAME=... OVERKIZ_PASSWORD=... uv run utils/fetch_server_data.py --server somfy_europe
OVERKIZ_USERNAME=... OVERKIZ_PASSWORD=... uv run utils/fetch_server_data.py --server atlantic_cozytouch
```

**What it fetches:**

- Protocol types (`/reference/protocolTypes`)
- UI classes, widgets, classifiers (`/reference/ui/...`)
- UI profile names and details (`/reference/ui/profileNames`, `/reference/ui/profile/<name>`)
- Device types per protocol (`/reference/devices/search`)
- Controllable definitions (`/reference/controllable/<name>`)

**Output:** `docs/data/<server>.json`

The script includes rate-limit handling with exponential backoff (starts at 10s, doubles per retry, up to 5 attempts).

## generate_enums.py

Generates all enum source files from the stored server data. No API calls — works entirely offline.

```bash
uv run utils/generate_enums.py
```

**Generates:**

| File | Source |
|------|--------|
| `pyoverkiz/enums/protocol.py` | `referenceMetadata.protocolTypes` |
| `pyoverkiz/enums/ui.py` | `referenceMetadata.uiClasses`, `uiWidgets`, `uiClassifiers` |
| `pyoverkiz/enums/ui_profile.py` | `referenceMetadata.uiProfiles` |
| `pyoverkiz/enums/command.py` | `protocols.*.commands` + `tests/fixtures/setup/*.json` |
| `docs/ui-profiles.md` | `referenceMetadata.uiProfiles` |

Data from all available server files is merged (union of all values). Hardcoded entries for protocols and widgets not found on any server are appended.

## generate_device_catalog.py

Generates the device types documentation page from stored server data. No API calls.

```bash
uv run utils/generate_device_catalog.py
```

**Generates:** `docs/device-types.md`

Merges device types from all server JSON files, deduplicates entries with identical interfaces, and enriches them with controllable definitions (discrete state values, data properties).

## mask_fixtures.py

Strips sensitive data (device URLs, gateway IDs, etc.) from test fixture files.

```bash
uv run utils/mask_fixtures.py
```

Processes all JSON files in `tests/fixtures/setup/` using the library's built-in obfuscation logic.

## Per-server JSON schema

Each file in `docs/data/` follows this structure:

```json
{
  "server": "somfy_europe",
  "referenceMetadata": {
    "controllableTypes": [{"id": 1, "name": "ACTUATOR", "label": "Actuator"}, ...],
    "protocolTypes": [{"id": 1, "prefix": "io", "name": "IO", "label": "IO HomeControl©"}, ...],
    "uiClasses": ["Alarm", "Light", ...],
    "uiWidgets": ["AlarmPanelController", ...],
    "uiClassifiers": ["alarm", ...],
    "uiProfiles": {
      "Alarm": {"name": "Alarm", "formFactor": false, "commands": [...], "states": [...]},
      ...
    }
  },
  "protocols": {
    "IO": [
      {
        "typeId": 1, "uiClass": "RollerShutter", "uiWidget": "...",
        "controllableName": "io:RollerShutterGenericComponent",
        "controllableType": "ACTUATOR",
        "commands": [{"commandName": "open", "nparams": 0, ...}],
        "states": [{"name": "ClosureState", "type": "ContinuousState", ...}],
        ...
      }
    ]
  },
  "controllableDefinitions": {
    "io:RollerShutterGenericComponent": {
      "commands": [...], "states": [...], "dataProperties": [...], ...
    }
  }
}
```

## Adding a new server

1. Get credentials for the server
2. Run `fetch_server_data.py --server <server_name>`
3. Commit the new `docs/data/<server>.json`
4. Run `generate_enums.py` and `generate_device_catalog.py` to regenerate code and docs
