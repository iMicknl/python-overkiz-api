# Diagnostics: Add Action Groups Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand `get_diagnostic_data()` to return a structured dict containing both setup and action group data, with per-section obfuscation.

**Architecture:** The method fetches two API endpoints (`setup` and `actionGroups`) concurrently using `asyncio.gather`, wraps them in a `{"setup": ..., "action_groups": [...]}` dict, and applies `obfuscate_sensitive_data` to each section individually. The obfuscation function is extended to accept lists of dicts in addition to plain dicts.

**Tech Stack:** Python 3.12+, aiohttp, pytest, pytest-asyncio

---

### Task 1: Extend `obfuscate_sensitive_data` to accept lists

**Files:**
- Modify: `pyoverkiz/obfuscate.py:27-68`
- Test: `tests/test_obfuscate.py`

- [ ] **Step 1: Write failing test for list input**

Add to `tests/test_obfuscate.py`:

```python
def test_obfuscate_list_of_dicts(self):
    """Ensure obfuscate_sensitive_data handles a list of dicts."""
    data = [
        {"label": "My Scene", "oid": "abc-123"},
        {"label": "Night Mode", "deviceURL": "io://1234-5678-1234/12345678"},
    ]
    result = obfuscate_sensitive_data(data)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["label"] != "My Scene"
    assert result[0]["oid"] == "abc-123"  # oid is not a sensitive key
    assert result[1]["label"] != "Night Mode"
    assert result[1]["deviceURL"] != "io://1234-5678-1234/12345678"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_obfuscate.py::TestObfucscateSensitive::test_obfuscate_list_of_dicts -v`
Expected: FAIL — `TypeError` because `obfuscate_sensitive_data` calls `.items()` on a list.

- [ ] **Step 3: Implement list support in `obfuscate_sensitive_data`**

In `pyoverkiz/obfuscate.py`, change the function signature and add a list guard at the top:

```python
def obfuscate_sensitive_data(
    data: dict[str, Any] | list[dict[str, Any]],
) -> dict[str, Any] | list[dict[str, Any]]:
    """Mask Overkiz JSON data to remove sensitive data."""
    if isinstance(data, list):
        return [obfuscate_sensitive_data(item) for item in data]

    mask_next_value = False
    # ... rest unchanged ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_obfuscate.py -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pyoverkiz/obfuscate.py tests/test_obfuscate.py
git commit -m "Support list input in obfuscate_sensitive_data"
```

---

### Task 2: Update `get_diagnostic_data()` to return structured dict

**Files:**
- Modify: `pyoverkiz/client.py:332-348`
- Test: `tests/test_client.py`

- [ ] **Step 1: Write failing test for new return shape**

Add to `tests/test_client.py` in the `TestOverkizClient` class. This test verifies the new return shape contains both `setup` and `action_groups` keys:

```python
@pytest.mark.asyncio
async def test_get_diagnostic_data_returns_structured_dict(self, client: OverkizClient):
    """Verify diagnostic data returns a dict with setup and action_groups sections."""
    with (CURRENT_DIR / "fixtures" / "setup" / "setup_tahoma_1.json").open(
        encoding="utf-8",
    ) as setup_mock:
        setup_resp = MockResponse(setup_mock.read())

    with (CURRENT_DIR / "fixtures" / "action_groups" / "action-group-tahoma-switch.json").open(
        encoding="utf-8",
    ) as ag_mock:
        ag_resp = MockResponse(ag_mock.read())

    responses = iter([setup_resp, ag_resp])

    with patch.object(aiohttp.ClientSession, "get", side_effect=lambda *a, **kw: next(responses)):
        diagnostics = await client.get_diagnostic_data(mask_sensitive_data=False)

    assert "setup" in diagnostics
    assert "action_groups" in diagnostics
    assert isinstance(diagnostics["action_groups"], list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_client.py::TestOverkizClient::test_get_diagnostic_data_returns_structured_dict -v`
Expected: FAIL — current implementation returns flat setup dict without `action_groups` key.

- [ ] **Step 3: Implement the new `get_diagnostic_data`**

Replace the method body in `pyoverkiz/client.py`:

```python
@retry_on_auth_error
async def get_diagnostic_data(self, mask_sensitive_data: bool = True) -> dict[str, Any]:
    """Get diagnostic data for the connected user setup.

        -> gateways data (serial number, activation state, ...): <gateways/gateway>
        -> setup location: <location>
        -> house places (rooms and floors): <place>
        -> setup devices: <devices>
        -> action groups: <actionGroups>

    By default, this data is masked to not return confidential or PII data.
    Set `mask_sensitive_data` to `False` to return the raw payloads.
    """
    setup = await self._get("setup")
    action_groups = await self._get("actionGroups")

    if mask_sensitive_data:
        setup = obfuscate_sensitive_data(setup)
        action_groups = obfuscate_sensitive_data(action_groups)

    return {
        "setup": setup,
        "action_groups": action_groups,
    }
```

Also add `Any` to the `typing` import at the top of `client.py` if not already present.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_client.py::TestOverkizClient::test_get_diagnostic_data_returns_structured_dict -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyoverkiz/client.py tests/test_client.py
git commit -m "Return structured dict from get_diagnostic_data with action groups"
```

---

### Task 3: Fix existing diagnostic tests for new return shape

**Files:**
- Modify: `tests/test_client.py:301-346`

The three existing diagnostic tests need updating to account for the new return shape (two API calls instead of one, structured dict output).

- [ ] **Step 1: Update `test_get_diagnostic_data`**

This parametrized test currently mocks a single `GET` call. It now needs to mock two (setup + actionGroups). Update to:

```python
@pytest.mark.asyncio
async def test_get_diagnostic_data(self, client: OverkizClient, fixture_name: str):
    """Verify that diagnostic data can be fetched and is not empty."""
    with (CURRENT_DIR / "fixtures" / "setup" / fixture_name).open(
        encoding="utf-8",
    ) as setup_mock:
        setup_resp = MockResponse(setup_mock.read())

    with (CURRENT_DIR / "fixtures" / "action_groups" / "action-group-tahoma-switch.json").open(
        encoding="utf-8",
    ) as ag_mock:
        ag_resp = MockResponse(ag_mock.read())

    responses = iter([setup_resp, ag_resp])

    with patch.object(aiohttp.ClientSession, "get", side_effect=lambda *a, **kw: next(responses)):
        diagnostics = await client.get_diagnostic_data()
        assert diagnostics
        assert "setup" in diagnostics
        assert "action_groups" in diagnostics
```

- [ ] **Step 2: Update `test_get_diagnostic_data_redacted_by_default`**

This test patches `obfuscate_sensitive_data` and needs to account for it being called twice (once for setup, once for action_groups):

```python
@pytest.mark.asyncio
async def test_get_diagnostic_data_redacted_by_default(self, client: OverkizClient):
    """Ensure diagnostics are redacted when no argument is provided."""
    with (CURRENT_DIR / "fixtures" / "setup" / "setup_tahoma_1.json").open(
        encoding="utf-8",
    ) as setup_mock:
        setup_resp = MockResponse(setup_mock.read())

    with (CURRENT_DIR / "fixtures" / "action_groups" / "action-group-tahoma-switch.json").open(
        encoding="utf-8",
    ) as ag_mock:
        ag_resp = MockResponse(ag_mock.read())

    responses = iter([setup_resp, ag_resp])

    with (
        patch.object(aiohttp.ClientSession, "get", side_effect=lambda *a, **kw: next(responses)),
        patch(
            "pyoverkiz.client.obfuscate_sensitive_data",
            return_value={"masked": True},
        ) as obfuscate,
    ):
        diagnostics = await client.get_diagnostic_data()
        assert diagnostics == {
            "setup": {"masked": True},
            "action_groups": {"masked": True},
        }
        assert obfuscate.call_count == 2
```

- [ ] **Step 3: Update `test_get_diagnostic_data_without_masking`**

```python
@pytest.mark.asyncio
async def test_get_diagnostic_data_without_masking(self, client: OverkizClient):
    """Ensure diagnostics can be returned without masking when requested."""
    with (CURRENT_DIR / "fixtures" / "setup" / "setup_tahoma_1.json").open(
        encoding="utf-8",
    ) as setup_mock:
        raw_setup = setup_mock.read()
        setup_resp = MockResponse(raw_setup)

    with (CURRENT_DIR / "fixtures" / "action_groups" / "action-group-tahoma-switch.json").open(
        encoding="utf-8",
    ) as ag_mock:
        raw_ag = ag_mock.read()
        ag_resp = MockResponse(raw_ag)

    responses = iter([setup_resp, ag_resp])

    with (
        patch.object(aiohttp.ClientSession, "get", side_effect=lambda *a, **kw: next(responses)),
        patch("pyoverkiz.client.obfuscate_sensitive_data") as obfuscate,
    ):
        diagnostics = await client.get_diagnostic_data(mask_sensitive_data=False)
        assert diagnostics == {
            "setup": json.loads(raw_setup),
            "action_groups": json.loads(raw_ag),
        }
        obfuscate.assert_not_called()
```

- [ ] **Step 4: Run all diagnostic tests**

Run: `pytest tests/test_client.py -k "diagnostic" -v`
Expected: All 20+ parametrized tests PASS.

- [ ] **Step 5: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/test_client.py
git commit -m "Update diagnostic tests for structured return shape"
```

---

### Task 4: Document the breaking change in migration guide

**Files:**
- Modify: `docs/migration-v2.md`

- [ ] **Step 1: Add diagnostics section to migration guide**

Add a new section after the "Executing commands" section (around line 100) in `docs/migration-v2.md`:

```markdown
## Diagnostics

`get_diagnostic_data()` now returns a structured dict with named sections instead of a flat setup dump.

| v1 | v2 |
|----|-----|
| `data["gateways"]` | `data["setup"]["gateways"]` |
| (not available) | `data["action_groups"]` |

=== "v1"

    ```python
    diagnostics = await client.get_diagnostic_data()
    gateways = diagnostics["gateways"]
    ```

=== "v2"

    ```python
    diagnostics = await client.get_diagnostic_data()
    gateways = diagnostics["setup"]["gateways"]
    action_groups = diagnostics["action_groups"]
    ```
```

- [ ] **Step 2: Commit**

```bash
git add docs/migration-v2.md
git commit -m "Document get_diagnostic_data breaking change in migration guide"
```
