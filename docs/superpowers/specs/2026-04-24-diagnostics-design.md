# Diagnostics: Add Action Groups and Structured Return Shape

## Context

PR #1476 proposed adding action groups (scenarios) to `get_diagnostic_data()`. The reviewer flagged two issues: action groups weren't being obfuscated despite the method's PII-masking contract, and the return shape change would silently break downstream callers. Since v2 is a breaking release, we can fix both properly.

## Design

### Return shape

`get_diagnostic_data()` returns a dict with named sections:

```python
{
    "setup": { ... },         # raw JSON from GET /setup
    "action_groups": [ ... ]  # raw JSON from GET /actionGroups
}
```

Keys are snake_case. Each section maps directly to one API endpoint. Adding future sections (execution history, places, setup options) is just adding a key.

### Method signature

```python
async def get_diagnostic_data(self, mask_sensitive_data: bool = True) -> dict[str, Any]:
```

- `mask_sensitive_data` defaults to `True`, obfuscating each section individually
- Return type narrows from `JSON` (union of dict and list) to `dict[str, Any]`

### Obfuscation

`obfuscate_sensitive_data` currently accepts only `dict[str, Any]`. Action groups come back as a JSON array. The function signature is updated to accept `dict[str, Any] | list[dict[str, Any]]`:

- If given a dict, behaves as before (recursive key-value masking)
- If given a list, iterates and obfuscates each dict element

This keeps the obfuscation logic centralized rather than scattering list-iteration across callers.

### Breaking changes

- Return shape changes from flat setup dict to `{"setup": ..., "action_groups": ...}`
- Downstream callers (e.g. HA integration) accessing `data["gateways"]` must update to `data["setup"]["gateways"]`

### What stays the same

- `mask_sensitive_data` parameter with `True` default
- Single method call convenience for getting a complete diagnostic dump
- All existing obfuscation rules (gatewayId, deviceURL, label, city, etc.)

## Files to modify

- `pyoverkiz/client.py` - `get_diagnostic_data()`: fetch both endpoints, structure return dict, apply per-section obfuscation
- `pyoverkiz/obfuscate.py` - `obfuscate_sensitive_data()`: accept list in addition to dict
- `tests/test_obfuscate.py` (if exists) or new test - verify list input handling
- `docs/migration-v2.md` - document the return shape change

## Out of scope

- Adding execution history, places, or other sections (future work)
- Changes to the HA integration (separate repo, separate PR)
- New obfuscation rules beyond what already exists
