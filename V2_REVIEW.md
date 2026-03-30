# pyoverkiz v2 - Comprehensive Review & Task List

## Executive Summary

This document reviews `pyoverkiz` (v2/main branch) and its primary consumer, the Home Assistant `overkiz` integration, to identify improvements for a professional v2 release. The review covers architecture, models, client API, enums, authentication, dependencies, typing, and integration friction points.

The v2 branch already has good progress:
- Python 3.12+ minimum, StrEnum throughout
- Auth strategies refactored with Credentials classes
- ActionGroup/ActionQueue pattern for command batching
- `UnknownEnumMixin` for graceful unknown enum handling
- Device helper methods added (`supports_command`, `get_state_value`, etc.)

---

## Table of Contents

1. [Models & Serialization](#1-models--serialization)
2. [Client API](#2-client-api)
3. [Enums](#3-enums)
4. [Authentication](#4-authentication)
5. [Dependencies](#5-dependencies)
6. [Type Safety & Typing](#6-type-safety--typing)
7. [Package Standards](#7-package-standards)
8. [HA Integration Friction Points](#8-ha-integration-friction-points)
9. [Task List](#9-task-list)

---

## 1. Models & Serialization

### 1.1 Dual `__init__` + attrs pattern is excessively verbose

Every model class uses `@define(init=False, kw_only=True)` and then manually writes a full `__init__` to handle `dict[str, Any] -> model` conversion. This means every field is defined **twice**: once as a class attribute and once as an `__init__` parameter.

**Example** - `Location` class (models.py:83-148): 18 fields defined as class attributes, then all 18 repeated in `__init__` with identical defaults, then all 18 assigned with `self.x = x`.

This pattern:
- Is ~3x more verbose than necessary
- Violates DRY - field changes require updates in two places
- Makes it easy to introduce bugs (miss a field, mismatch defaults)
- Doesn't leverage attrs' key feature: auto-generated `__init__`

**Recommendation:** Use a proper serialization approach. Options:
- **attrs + cattrs** (minimal change): Keep `@define`, use cattrs for `dict -> model` conversion with structure hooks for nested types and camelCase handling
- **msgspec** (fastest): `msgspec.Struct` with `rename="camel"` handles camelCase natively, is the fastest Python serialization lib
- **dataclasses + dacite/cattrs**: Drop attrs dependency entirely since Python 3.12+ dataclasses are sufficient
- **pydantic v2**: Full validation + serialization, heavier but widely understood

### 1.2 `**_: Any` kwargs swallowing

Every `__init__` ends with `**_: Any`, silently discarding unknown keys from the API. This hides:
- New API fields the library should surface
- Typos in field names during development
- API schema changes that might indicate breaking changes

**Recommendation:** Log unknown fields at DEBUG level, or use a serialization lib that handles unknown fields explicitly (e.g., `forbid_unknown_fields=False` with logging).

### 1.3 Giant monolithic `models.py`

The `models.py` file is 1380 lines containing 30+ classes. Finding a specific model requires scrolling through unrelated types.

**Recommendation:** Split into a `models/` package:
```
models/
  __init__.py      # re-exports
  setup.py         # Setup, Location, Place, Zone, Feature
  device.py        # Device, DeviceIdentifier, Definition, States, State
  command.py       # Command, Action, ActionGroup, CommandDefinition(s)
  execution.py     # Execution, HistoryExecution, HistoryExecutionCommand
  gateway.py       # Gateway, Partner, Connectivity
  server.py        # ServerConfig, ProtocolType
  ui_profile.py    # UIProfileDefinition, UIProfileCommand, etc.
```

### 1.4 States/CommandDefinitions containers have non-standard `__getitem__`

`States.__getitem__` returns `State | None` instead of raising `KeyError`. This breaks the Python mapping protocol contract. The `get` method is aliased to `__getitem__` but should have its own semantics.

HA code like `device.states[state_name]` works but is confusing - it returns `None` rather than raising `KeyError`.

**Recommendation:** Make `__getitem__` raise `KeyError` on missing items (standard behavior), keep `get()` for `None`-returning lookups. Or better: make `States` implement `Mapping[str, State]` properly.

### 1.5 `State.value` is a broad union type

`StateType = str | int | float | bool | dict[str, Any] | list[Any] | None`

Every consumer has to `cast()` the value to the expected type. The typed accessors (`value_as_int`, `value_as_float`) exist but are on `State`, not easily accessible from `Device`.

**Recommendation:** Expose convenience on `Device`:
```python
def get_state_int(self, state: str) -> int | None: ...
def get_state_float(self, state: str) -> float | None: ...
def get_state_str(self, state: str) -> str | None: ...
def get_state_bool(self, state: str) -> bool | None: ...
```

---

## 2. Client API

### 2.1 No convenience `execute_command()` method

The most common pattern in HA is: send **one command to one device**. The v2 API requires:
```python
action = Action(device_url, [Command("open")])
await client.execute_action_group([action])
```

HA's `OverkizExecutor.async_execute_command()` wraps this 3-object construction. This convenience should live in the library.

**Recommendation:** Add a helper method:
```python
async def execute_command(
    self,
    device_url: str,
    command: Command,
    label: str | None = "python-overkiz-api",
) -> str:
    """Execute a single command on a single device (convenience wrapper)."""
    action = Action(device_url, [command])
    return await self.execute_action_group([action], label=label)
```

### 2.2 `check_response` is a 100-line if/else chain

`client.py:769-880` uses string matching (`message.startswith(...)`, `"foo" in message`) to classify errors. This is fragile and hard to maintain.

**Recommendation:** Use a mapping/registry pattern:
```python
_ERROR_PATTERNS: list[tuple[Callable[[str], bool], type[BaseOverkizException]]] = [
    (lambda m: m.startswith("Another action exists"), DuplicateActionOnDeviceException),
    (lambda m: "Too many requests" in m, TooManyRequestsException),
    (lambda m: m == "Bad credentials", BadCredentialsException),
    # ...
]
```

Also consider matching on `errorCode` first (more reliable), then falling back to message matching.

### 2.3 `humps.decamelize()` called at every deserialization site

Every method that returns a model does:
```python
response = await self.__get("some/path")
model = SomeModel(**humps.decamelize(response))
```

The `humps.decamelize()` call is repeated 15+ times.

**Recommendation:** Centralize in a generic deserializer or move `decamelize` into the HTTP methods (`__get`, `__post`). Or use a serialization lib that handles case conversion natively.

### 2.4 Client holds mutable shared state

`self.devices`, `self.gateways`, `self.setup` are mutable lists/objects that cache API responses. Methods like `get_devices()` return the cache by default and mutate it on refresh. This creates subtle bugs:
- Multiple callers can hold stale references
- No thread-safety guarantees
- Cache invalidation is ad-hoc

**Recommendation:** Consider making the client stateless or at minimum making caching opt-in. The coordinator in HA manages its own device state anyway.

### 2.5 Retry decorators are module-level globals

The `backoff` decorators (`retry_on_auth_error`, etc.) are defined as module-level variables and applied to methods. This:
- Makes retry behavior non-configurable per client instance
- Complicates testing (can't mock retry behavior)
- Couples retry strategy to the module level

**Recommendation:** Move retry logic into the client class or make it configurable at init time.

### 2.6 No configurable request timeouts

The client uses aiohttp with default timeouts. Long-running or hung connections can block indefinitely.

**Recommendation:** Accept a `timeout: aiohttp.ClientTimeout` parameter in the constructor, with sensible defaults (e.g., 30s total, 10s connect).

### 2.7 `server` property on client returns `ServerConfig`

HA accesses `client.server.manufacturer` and `client.server.configuration_url`. The attribute name `server_config` in v2 is clearer but HA still uses `client.server`. Consider whether to provide both or just rename.

---

## 3. Enums

### 3.1 Auto-generated enum files are massive but necessary

`command.py` (774 lines), `state.py` (404 lines), `ui.py` (477 lines), `ui_profile.py` (1817 lines). These are generated from API metadata and are essential for type-safe code in HA.

**Status:** Already well-handled with `generate_enums.py` utility. No changes needed for the enum content itself.

### 3.2 `GatewayType.beautify_name` is useful

HA uses `gateway.type.beautify_name` for display. This kind of enum-level helper is good practice.

**Recommendation:** Consider adding similar helpers to other enums where HA does manual string formatting.

### 3.3 Enums could have docstrings per member

For the most commonly-used enums (UIClass, UIWidget), docstrings on members would help developers understand which widget maps to which physical device.

---

## 4. Authentication

### 4.1 Auth refactoring is already good

The `auth/` module with `AuthStrategy` protocol, credential classes, and factory pattern is well-designed. The separation of concerns is clean.

### 4.2 `boto3` + `warrant-lite` are heavy deps for Nexity only

`boto3` pulls in `botocore` (~70MB installed). This is a massive dependency for a feature only Nexity users need.

**Recommendation:** Make `boto3` and `warrant-lite` optional extras:
```toml
[project.optional-dependencies]
nexity = ["boto3<2.0.0,>=1.18.59", "warrant-lite<2.0.0,>=1.0.4"]
```
Then do lazy imports in `NexityAuthStrategy` with a helpful error message if not installed.

### 4.3 `NexityAuthStrategy` uses blocking `asyncio.get_event_loop()`

```python
loop = asyncio.get_event_loop()
client = await loop.run_in_executor(None, _client)
```

Should use `asyncio.get_running_loop()` (deprecated since 3.10 to use `get_event_loop()` without a running loop).

---

## 5. Dependencies

### 5.1 Current dependencies assessment

| Dependency | Purpose | Assessment |
|---|---|---|
| `aiohttp` | HTTP client | Essential, keep |
| `pyhumps` | camelCase conversion | Could be replaced by serialization lib or simple utility |
| `backoff` | Retry logic | Good, but consider `tenacity` for more flexibility |
| `attrs` | Model definitions | Under-utilized (custom `__init__` everywhere). Drop or use properly |
| `boto3` | Nexity AWS Cognito | Heavy, make optional |
| `warrant-lite` | Nexity SRP auth | Heavy, make optional |

### 5.2 `pyhumps` can be eliminated

If using a serialization lib with camelCase support (msgspec, pydantic, cattrs with rename), `pyhumps` is no longer needed. Even without a serialization lib, a simple 10-line snake_case/camelCase converter would suffice.

### 5.3 `attrs` is used as a glorified dataclass

With Python 3.12+ as minimum, `@dataclass(slots=True, kw_only=True)` provides the same features used from attrs (`@define`). Every class uses `init=False` which defeats attrs' main advantage.

**Recommendation:** Either fully leverage attrs (use converters, validators, `@define` with auto-init) or switch to stdlib dataclasses to reduce dependencies.

---

## 6. Type Safety & Typing

### 6.1 No `py.typed` marker

Package doesn't include a `py.typed` marker file (PEP 561). Type checkers and IDEs won't use the package's type annotations.

**Recommendation:** Add `pyoverkiz/py.typed` (empty file) and include it in the package build.

### 6.2 `JSON` type alias is too broad

```python
JSON = dict[str, Any] | list[dict[str, Any]]
```

This is used for both request payloads and responses. More specific types would improve IDE support and catch bugs.

### 6.3 `mypy` configured with `ignore_missing_imports = true`

This effectively disables half of mypy's value. Should fix missing stubs or add type stubs for dependencies.

### 6.4 Response types are `Any`

`__get` and `__post` return `Any`. Every caller has to know the expected shape. Consider generic typed wrappers or at least document expected response shapes.

### 6.5 Missing `__all__` exports

`models.py` and the top-level `__init__.py` don't define `__all__`, making it unclear what's part of the public API.

**Recommendation:** Add `__all__` to all public modules and re-export key types from `pyoverkiz/__init__.py`:
```python
from pyoverkiz.client import OverkizClient
from pyoverkiz.models import Device, Command, Action, ...
from pyoverkiz.exceptions import OverkizException, ...
```

---

## 7. Package Standards

### 7.1 Missing from top-level `__init__.py`

The package `__init__.py` only has a docstring. Professional packages re-export their key classes for convenient imports:
```python
from pyoverkiz import OverkizClient, Device, Command
```
Instead of:
```python
from pyoverkiz.client import OverkizClient
from pyoverkiz.models import Device, Command
```

### 7.2 No `__version__` attribute

Users can't do `pyoverkiz.__version__`. Use `importlib.metadata` for zero-config version exposure:
```python
from importlib.metadata import version
__version__ = version("pyoverkiz")
```

### 7.3 Missing CHANGELOG

A v2 release with breaking changes absolutely needs a CHANGELOG documenting what changed, what was renamed, and migration steps.

### 7.4 README needs v2 migration guide

For HA and other consumers, a clear migration guide from v1 to v2 API is essential.

### 7.5 Pre-commit / CI

The project has `prek` (rust-based pre-commit) and ruff configured. The lint rules are comprehensive (D, ASYNC, E, F, UP, B, SIM, I, RUF, S, T, C4). Good baseline.

---

## 8. HA Integration Friction Points

These are patterns in HA's `overkiz` integration that reveal where pyoverkiz's API falls short.

### 8.1 OverkizExecutor duplicates Device helpers

HA's `executor.py` provides:
- `select_command(*commands)` -> now on `Device.select_first_command()`
- `has_command(*commands)` -> now on `Device.supports_any_command()`
- `select_state(*states)` -> now on `Device.select_first_state_value()`
- `has_state(*states)` -> now on `Device.has_any_state_value()`
- `select_attribute(*attributes)` -> now on `Device.select_first_attribute_value()`
- `select_definition_state(*states)` -> now on `Device.select_first_state_definition()`

The v2 Device model already added these! But the signatures differ slightly:
- HA uses `*args` (variadic), v2 uses `list[str]` parameter
- Consider accepting both patterns, or standardize on variadic (more ergonomic for callers)

**Recommendation:** Consider `*args` style for the most-used Device helpers:
```python
def get_state_value(self, *states: str) -> StateType | None:
```

### 8.2 `device.protocol` shortcut missing

HA uses `device.protocol` frequently (coordinator.py:72, executor.py:97). In v2 this is `device.identifier.protocol`. Should add a convenience property.

```python
@property
def protocol(self) -> Protocol:
    return self.identifier.protocol
```

### 8.3 `device.base_device_url` needed

HA computes `base_device_url = device_url.split("#")[0]` in multiple places (entity.py:32, executor.py:37, coordinator.py:195). In v2, `DeviceIdentifier` has `base_device_url` but it's not directly on `Device`.

**Recommendation:** Add `Device.base_device_url` property:
```python
@property
def base_device_url(self) -> str:
    return self.identifier.base_device_url
```

### 8.4 `device.is_sub_device` needed

HA's entity.py:52-54 checks `"#" in self.device_url and not self.device_url.endswith("#1")`. This is already on `DeviceIdentifier.is_sub_device` in v2 but not exposed on `Device`.

**Recommendation:** Add `Device.is_sub_device` property.

### 8.5 `device.gateway_id` shortcut needed

HA's executor.py:168-174 parses the device URL to extract gateway_id. In v2, `DeviceIdentifier.gateway_id` exists. Expose on `Device`.

### 8.6 `cast(int, value)` everywhere

HA casts state values constantly:
```python
return 100 - cast(int, position)                    # cover
return (cast(int, red), cast(int, green), cast(int, blue))  # light
return round(cast(int, value) * 255 / 100)          # light
```

The root cause is `StateType` being a broad union. Adding typed getters to `Device` would eliminate most casts:
```python
# Instead of:
cast(int, self.executor.select_state(OverkizState.CORE_CLOSURE))
# Would become:
device.get_state_int(OverkizState.CORE_CLOSURE)
```

### 8.7 async_cancel_command accesses action_group as dict

`executor.py:143-156` has a comment: "executions.action_group is typed incorrectly in the upstream library". The code does `execution.action_group.get("actions")` treating it as a dict, but in v2 it's a proper `ActionGroup` object.

This should be fixed on both sides in v2.

### 8.8 Widget/UIClass properties can raise ValueError

`Device.widget` and `Device.ui_class` raise `ValueError` if not set. HA code like:
```python
OVERKIZ_DEVICE_TO_PLATFORM.get(device.widget) or OVERKIZ_DEVICE_TO_PLATFORM.get(device.ui_class)
```
Would crash if neither is set. Should return `None` or have a safe variant.

**Recommendation:** Make `widget` and `ui_class` return `UIWidget | None` and `UIClass | None` respectively. Or add `widget_or_none` / `ui_class_or_none` safe variants.

### 8.9 HA needs `client.server` (not `client.server_config`)

HA accesses `client.server.manufacturer`, `client.server.configuration_url`. The v2 rename to `server_config` is fine internally but consider a `server` property alias for backwards compatibility, or document the rename clearly.

### 8.10 Missing `Scenario` type alias

HA imports `Scenario` from pyoverkiz. In v2 this was renamed to `ActionGroup`. The rename is correct but needs clear documentation.

---

## 9. Task List

### Quick Wins (non-breaking or minor changes)

| # | Task | Files | Effort |
|---|---|---|---|
| Q1 | Add `py.typed` marker file | `pyoverkiz/py.typed` | Trivial |
| Q2 | Add `__version__` via `importlib.metadata` | `pyoverkiz/__init__.py` | Trivial |
| Q3 | Add `__all__` exports to all public modules | `models.py`, `__init__.py`, `client.py` | Small |
| Q4 | Re-export key classes from `pyoverkiz/__init__.py` | `pyoverkiz/__init__.py` | Small |
| Q5 | Add `Device.protocol` property shortcut | `models.py` | Trivial |
| Q6 | Add `Device.base_device_url` property | `models.py` | Trivial |
| Q7 | Add `Device.is_sub_device` property | `models.py` | Trivial |
| Q8 | Add `Device.gateway_id` property | `models.py` | Trivial |
| Q9 | Add typed state getters on Device (`get_state_int`, `get_state_float`, `get_state_str`, `get_state_bool`) | `models.py` | Small |
| Q10 | Add `execute_command()` convenience method on client | `client.py` | Small |
| Q11 | Make `Device.widget` and `Device.ui_class` return `None` instead of raising | `models.py` | Small |
| Q12 | Use `asyncio.get_running_loop()` in NexityAuthStrategy | `auth/strategies.py` | Trivial |
| Q13 | Add configurable request timeout to client | `client.py` | Small |
| Q14 | Change Device helper signatures from `list[str]` to `*args: str` for ergonomics | `models.py` | Small |
| Q15 | Add `server` property alias on client for `server_config` | `client.py` | Trivial |

### Refactor (breaking changes, larger effort)

| # | Task | Files | Effort |
|---|---|---|---|
| R1 | Replace attrs + manual `__init__` with proper serialization (cattrs, msgspec, or pydantic) | All models | Large |
| R2 | Split `models.py` into `models/` package | `models.py` -> `models/` | Medium |
| R3 | Extract `check_response` error matching into a mapping/registry | `client.py` | Medium |
| R4 | Centralize `humps.decamelize()` into HTTP methods or serializer | `client.py` | Medium |
| R5 | Make `boto3` + `warrant-lite` optional dependencies (extras) | `pyproject.toml`, `auth/strategies.py`, `auth/factory.py` | Medium |
| R6 | Eliminate `pyhumps` dependency (replace with serialization lib or simple utility) | `client.py`, `serializers.py` | Medium (tied to R1) |
| R7 | Drop `attrs` dependency if switching to dataclasses or another serialization lib | `models.py`, `pyproject.toml` | Large (tied to R1) |
| R8 | Fix `States.__getitem__` to follow mapping protocol (raise `KeyError`) | `models.py` | Small (breaking) |
| R9 | Make retry behavior configurable per client instance | `client.py` | Medium |
| R10 | Remove client-side mutable state caching or make it opt-in | `client.py` | Medium |
| R11 | Fix `mypy` config to not ignore missing imports | `pyproject.toml`, type stubs | Medium |
| R12 | Log unknown kwargs from API responses instead of silently discarding | All models | Small (tied to R1) |
| R13 | Write v2 CHANGELOG and migration guide | `CHANGELOG.md`, `README.md` | Medium |
| R14 | Add `CommandDefinitions` proper `Mapping` protocol support | `models.py` | Small |

### Dependency Reduction Summary

Current deps (v2): `aiohttp`, `pyhumps`, `backoff`, `attrs`, `boto3`, `warrant-lite`

After refactor:
- **Keep:** `aiohttp`, `backoff` (or `tenacity`)
- **Replace:** `pyhumps` + `attrs` -> one of: `cattrs`, `msgspec`, `pydantic` (or stdlib dataclasses with a small case-converter)
- **Optional:** `boto3`, `warrant-lite` -> move to `[nexity]` extra

Target: 2-3 required deps instead of 6.

### Priority Order

**Phase 1 - Quick wins (do first, low risk):**
Q1-Q15 can all be done independently and improve the developer experience immediately.

**Phase 2 - Serialization refactor (biggest impact):**
R1 + R6 + R7 together. This is the most impactful change - it will:
- Cut model code by ~60%
- Remove 2-3 dependencies
- Centralize camelCase handling
- Enable proper validation

**Phase 3 - Client cleanup:**
R3 + R4 + R9 + R10. Clean up the client API surface.

**Phase 4 - Documentation & polish:**
R13 + R11. Essential for the v2 release.

**Phase 5 - Optional deps:**
R5. Can be done anytime but should be before v2 release.

---

## Appendix: HA Import Changes Needed for v2

| v1 (current HA) | v2 (new) |
|---|---|
| `from pyoverkiz.models import Scenario` | `from pyoverkiz.models import ActionGroup` |
| `from pyoverkiz.models import OverkizServer` | `from pyoverkiz.models import ServerConfig` |
| `from pyoverkiz.utils import generate_local_server` | `from pyoverkiz.utils import create_local_server_config` |
| `OverkizClient(username=, password=, token=)` | `OverkizClient(credentials=UsernamePasswordCredentials(...))` |
| `client.execute_command(url, cmd, label)` | `client.execute_command(url, cmd, label)` (add convenience method Q10) |
| `client.get_scenarios()` | `client.get_action_groups()` |
| `client.server` | `client.server_config` (or add alias Q15) |
| `device.protocol` (direct) | `device.protocol` (needs property Q5) |
| `device_url.split("#")[0]` | `device.base_device_url` (needs property Q6) |
