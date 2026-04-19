#!/usr/bin/env python3
"""Probe real Overkiz cloud and local API endpoints with invalid inputs.

Tests that every error response is caught as a specific pyoverkiz exception
rather than crashing with an unhandled error, KeyError, etc.

Usage:
    # Cloud only (needs username/password):
    python scripts/test_error_handling.py \
        --server somfy_europe \
        --username you@example.com \
        --password secret

    # Local only (needs host + token):
    python scripts/test_error_handling.py \
        --local-host gateway-1234-5678-9012.local:8443 \
        --local-token YOUR_TOKEN

    # Both at once:
    python scripts/test_error_handling.py \
        --server somfy_europe \
        --username you@example.com \
        --password secret \
        --local-host gateway-1234-5678-9012.local:8443 \
        --local-token YOUR_TOKEN

Each probe is independent — a failure in one does not stop the rest.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import traceback
from dataclasses import dataclass, field

import aiohttp
from aiohttp import ClientSession, TraceConfig

from pyoverkiz.auth.credentials import (
    LocalTokenCredentials,
    UsernamePasswordCredentials,
)
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import APIType, Server
from pyoverkiz.exceptions import BaseOverkizError
from pyoverkiz.models import Action, Command, Execution
from pyoverkiz.utils import create_local_server_config

FAKE_DEVICE_URL = "io://0000-0000-0000/12345678"
FAKE_EXEC_ID = "00000000-0000-0000-0000-000000000000"
FAKE_OID = "00000000-0000-0000-0000-000000000000"
FAKE_OPTION = "nonExistentOption-0000-0000-0000"
FAKE_CONTROLLABLE = "io:NonExistentDeviceControllable"
FAKE_PROFILE = "NonExistentProfile"


# ── HTTP tracing ──────────────────────────────────────────────────────────────

# Collects full request/response details per-probe so they can be printed
# alongside the result.  Each entry is a dict with method, url, status,
# request/response headers, and response body.

_current_traces: list[dict] = []


async def _on_request_start(
    session: ClientSession,
    trace_ctx: object,
    params: aiohttp.TraceRequestStartParams,
) -> None:
    _current_traces.append(
        {
            "method": params.method,
            "url": str(params.url),
            "req_headers": dict(params.headers),
        }
    )


async def _on_request_end(
    session: ClientSession,
    trace_ctx: object,
    params: aiohttp.TraceRequestEndParams,
) -> None:
    # .text() caches the body internally, so the caller can still read it.
    body = await params.response.text()
    entry = {
        "status": params.response.status,
        "resp_headers": dict(params.response.headers),
        "resp_body": body,
    }
    if _current_traces:
        _current_traces[-1].update(entry)
    else:
        _current_traces.append(entry)


def _build_trace_config() -> TraceConfig:
    tc = TraceConfig()
    tc.on_request_start.append(_on_request_start)
    tc.on_request_end.append(_on_request_end)
    return tc


def _format_trace(trace: dict) -> str:
    lines: list[str] = []
    method = trace.get("method", "?")
    url = trace.get("url", "?")
    status = trace.get("status", "?")
    lines.append(f"    >>> {method} {url}")

    req_headers = trace.get("req_headers", {})
    for k, v in req_headers.items():
        if k.lower() in ("authorization", "cookie"):
            v = v[:20] + "..." if len(v) > 20 else v
        lines.append(f"        {k}: {v}")

    lines.append(f"    <<< {status}")

    resp_headers = trace.get("resp_headers", {})
    for k, v in resp_headers.items():
        lines.append(f"        {k}: {v}")

    body = trace.get("resp_body", "")
    if body:
        # Truncate very long bodies but keep enough to see the error
        if len(body) > 500:
            body = body[:500] + f"... ({len(body)} bytes total)"
        lines.append(f"        Body: {body}")

    return "\n".join(lines)


# ── Probe runner ──────────────────────────────────────────────────────────────


@dataclass
class ProbeResult:
    name: str
    api: str
    passed: bool
    kind: str = "error"
    exception_type: str = ""
    detail: str = ""
    traces: list[dict] = field(default_factory=list)


@dataclass
class ProbeRunner:
    results: list[ProbeResult] = field(default_factory=list)
    quiet: bool = False

    async def probe(self, name: str, api: str, coro):
        """Probe that expects a BaseOverkizError to be raised."""
        _current_traces.clear()
        try:
            await coro
            self.results.append(
                ProbeResult(
                    name=name,
                    api=api,
                    passed=False,
                    kind="error",
                    detail="Expected an error but call succeeded",
                    traces=list(_current_traces),
                )
            )
        except BaseOverkizError as exc:
            self.results.append(
                ProbeResult(
                    name=name,
                    api=api,
                    passed=True,
                    kind="error",
                    exception_type=type(exc).__name__,
                    detail=str(exc)[:200],
                    traces=list(_current_traces),
                )
            )
        except Exception as exc:
            self.results.append(
                ProbeResult(
                    name=name,
                    api=api,
                    passed=False,
                    kind="error",
                    exception_type=type(exc).__name__,
                    detail=str(exc)[:200],
                    traces=list(_current_traces),
                )
            )

    async def probe_graceful(self, name: str, api: str, coro, check=None):
        """Probe that expects no exception — the client should handle the
        response gracefully (return None, recover via retry, etc.).
        """
        _current_traces.clear()
        try:
            result = await coro
            detail = (
                f"Returned: {result!r}"[:200]
                if result is not None
                else "Returned: None"
            )
            ok = check(result) if check else True
            self.results.append(
                ProbeResult(
                    name=name,
                    api=api,
                    passed=ok,
                    kind="graceful",
                    detail=detail if ok else f"Check failed — {detail}",
                    traces=list(_current_traces),
                )
            )
        except Exception as exc:
            self.results.append(
                ProbeResult(
                    name=name,
                    api=api,
                    passed=False,
                    kind="graceful",
                    exception_type=type(exc).__name__,
                    detail=f"Expected graceful handling but got: {exc!s}"[:200],
                    traces=list(_current_traces),
                )
            )

    async def probe_command(self, name: str, api: str, coro):
        """Probe that expects a successful command execution returning an exec_id."""
        _current_traces.clear()
        try:
            result = await coro
            ok = isinstance(result, str) and len(result) > 0
            self.results.append(
                ProbeResult(
                    name=name,
                    api=api,
                    passed=ok,
                    kind="command",
                    detail=f"exec_id: {result}"
                    if ok
                    else f"Unexpected result: {result!r}",
                    traces=list(_current_traces),
                )
            )
        except Exception as exc:
            self.results.append(
                ProbeResult(
                    name=name,
                    api=api,
                    passed=False,
                    kind="command",
                    exception_type=type(exc).__name__,
                    detail=str(exc)[:200],
                    traces=list(_current_traces),
                )
            )

    def print_report(self):
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)

        kind_labels = {
            "error": "Error probes (expect BaseOverkizError)",
            "graceful": "Graceful handling probes (expect no crash)",
            "command": "Command probes (expect exec_id)",
        }

        print("\n" + "=" * 80)
        print(f"  PROBE RESULTS: {passed} passed, {failed} failed")
        print("=" * 80)

        for kind, label in kind_labels.items():
            kind_results = [r for r in self.results if r.kind == kind]
            if not kind_results:
                continue

            print(f"\n  --- {label} ---")
            for r in kind_results:
                status = "PASS" if r.passed else "FAIL"
                icon = "+" if r.passed else "-"
                exc_info = f" -> {r.exception_type}" if r.exception_type else ""
                print(f"\n  [{icon}] {status}  [{r.api:5s}] {r.name}{exc_info}")
                if r.detail:
                    print(f"           {r.detail}")

                if not self.quiet and r.traces:
                    for trace in r.traces:
                        print(_format_trace(trace))
                elif not self.quiet and not r.traces:
                    print("    (no HTTP trace captured)")

        print("\n" + "=" * 80)
        if failed:
            print(f"\n  {failed} probe(s) FAILED!")
        else:
            print("\n  All probes passed.")
        print()


async def probe_client(
    client: OverkizClient,
    api_label: str,
    runner: ProbeRunner,
    rts_device_url: str | None = None,
):
    """Run all probes against a single client instance.

    Args:
        rts_device_url: URL of a real RTS device to test commands on. RTS covers
            are fire-and-forget (no state feedback), so sending close/open/my/stop
            is safe even on real hardware — the worst that happens is a shutter moves.
    """
    # --- Sanity checks (run first to verify connectivity) ---

    try:
        devices = await client.get_devices(refresh=True)
        print(
            f"  [*] Sanity check [{api_label}]: get_devices returned {len(devices)} devices"
        )
    except Exception as exc:
        print(f"  [!] Sanity check [{api_label}]: get_devices FAILED: {exc}")

    try:
        executions = await client.get_current_executions()
        print(
            f"  [*] Sanity check [{api_label}]: get_current_executions returned {len(executions)} items"
        )
    except Exception as exc:
        print(f"  [!] Sanity check [{api_label}]: get_current_executions FAILED: {exc}")

    is_local = client.server_config.api_type == APIType.LOCAL

    # --- Error probes: expect BaseOverkizError ---

    await runner.probe(
        "get_state(fake device URL)",
        api_label,
        client.get_state(FAKE_DEVICE_URL),
    )

    await runner.probe(
        "get_device_definition(fake device URL)",
        api_label,
        client.get_device_definition(FAKE_DEVICE_URL),
    )

    await runner.probe(
        "get_setup_option_parameter(fake option, fake param)",
        api_label,
        client.get_setup_option_parameter(FAKE_OPTION, "fakeParam"),
    )

    await runner.probe(
        "get_reference_controllable(fake name)",
        api_label,
        client.get_reference_controllable(FAKE_CONTROLLABLE),
    )

    await runner.probe(
        "get_reference_ui_profile(fake profile)",
        api_label,
        client.get_reference_ui_profile(FAKE_PROFILE),
    )

    await runner.probe(
        "refresh_device_states(fake device URL)",
        api_label,
        client.refresh_device_states(FAKE_DEVICE_URL),
    )

    await runner.probe(
        "schedule_persisted_action_group(fake OID)",
        api_label,
        client.schedule_persisted_action_group(FAKE_OID, 9999999999),
    )

    # Local gateway returns error for fake options; cloud returns empty {}
    if is_local:
        await runner.probe(
            "get_setup_option(fake option)",
            api_label,
            client.get_setup_option(FAKE_OPTION),
        )
    else:
        await runner.probe_graceful(
            "get_setup_option(fake option)",
            api_label,
            client.get_setup_option(FAKE_OPTION),
            check=lambda result: result is None,
        )

    # Cloud rejects fake devices/OIDs; local gateway accepts them
    if is_local:
        await runner.probe_command(
            "execute_action_group(fake device + bad command)",
            api_label,
            client.execute_action_group(
                [
                    Action(
                        device_url=FAKE_DEVICE_URL,
                        commands=[Command(name="totallyFakeCommand", parameters=[42])],
                    )
                ]
            ),
        )

        await runner.probe_command(
            "execute_persisted_action_group(fake OID)",
            api_label,
            client.execute_persisted_action_group(FAKE_OID),
        )
    else:
        await runner.probe(
            "execute_action_group(fake device + bad command)",
            api_label,
            client.execute_action_group(
                [
                    Action(
                        device_url=FAKE_DEVICE_URL,
                        commands=[Command(name="totallyFakeCommand", parameters=[42])],
                    )
                ]
            ),
        )

        await runner.probe(
            "execute_persisted_action_group(fake OID)",
            api_label,
            client.execute_persisted_action_group(FAKE_OID),
        )

    # --- Graceful handling probes: expect no crash ---

    await runner.probe_graceful(
        "get_current_execution(fake exec_id)",
        api_label,
        client.get_current_execution(FAKE_EXEC_ID),
        check=lambda result: result is None,
    )

    await runner.probe_graceful(
        "cancel_execution(fake exec_id)",
        api_label,
        client.cancel_execution(FAKE_EXEC_ID),
    )

    saved_listener = client.event_listener_id

    client.event_listener_id = "totally-fake-listener-id"
    await runner.probe_graceful(
        "fetch_events(fake listener id) -> retry recovery",
        api_label,
        client.fetch_events(),
        check=lambda result: isinstance(result, list),
    )

    client.event_listener_id = saved_listener

    # Execution history is only available on cloud
    if not is_local:
        await runner.probe_graceful(
            "get_execution_history()",
            api_label,
            client.get_execution_history(),
            check=lambda result: isinstance(result, list) and len(result) > 0,
        )

    # --- RTS command probes: execute real commands on RTS covers ---

    if not rts_device_url:
        rts_device_url = _find_rts_device(client)

    if rts_device_url:
        print(f"  [*] Using RTS device: {rts_device_url}\n")
    else:
        print("  [*] No RTS device found, skipping command probes\n")

    if rts_device_url:
        last_exec_id: str | None = None

        for cmd_name in ("close", "my", "stop"):
            _current_traces.clear()
            try:
                exec_id = await client.execute_action_group(
                    [
                        Action(
                            device_url=rts_device_url,
                            commands=[Command(name=cmd_name)],
                        )
                    ]
                )
                ok = isinstance(exec_id, str) and len(exec_id) > 0
                runner.results.append(
                    ProbeResult(
                        name=f"execute_action_group(RTS {cmd_name})",
                        api=api_label,
                        passed=ok,
                        kind="command",
                        detail=f"exec_id: {exec_id}"
                        if ok
                        else f"Unexpected: {exec_id!r}",
                        traces=list(_current_traces),
                    )
                )
                if ok:
                    last_exec_id = exec_id
            except Exception as exc:
                runner.results.append(
                    ProbeResult(
                        name=f"execute_action_group(RTS {cmd_name})",
                        api=api_label,
                        passed=False,
                        kind="command",
                        exception_type=type(exc).__name__,
                        detail=str(exc)[:200],
                        traces=list(_current_traces),
                    )
                )

        if last_exec_id:

            def _check_execution(result):
                if result is None:
                    return True
                if not isinstance(result, Execution):
                    return False
                return result.action_group is not None

            await runner.probe_graceful(
                f"get_current_execution({last_exec_id[:8]}...)",
                api_label,
                client.get_current_execution(last_exec_id),
                check=_check_execution,
            )

            await runner.probe_graceful(
                "get_current_executions()",
                api_label,
                client.get_current_executions(),
                check=lambda result: isinstance(result, list),
            )


def _find_rts_device(client: OverkizClient) -> str | None:
    """Return the URL of the first RTS device, if any."""
    for device in client.devices:
        if device.device_url.startswith("rts://"):
            return device.device_url
    return None


async def run_cloud(args: argparse.Namespace, runner: ProbeRunner):
    server = Server(args.server)
    credentials = UsernamePasswordCredentials(args.username, args.password)

    trace_config = _build_trace_config()
    session = ClientSession(
        headers={"User-Agent": "python-overkiz-api"},
        trace_configs=[trace_config],
    )

    async with OverkizClient(
        server=server, credentials=credentials, session=session
    ) as client:
        print(f"\nLogging in to cloud ({args.server})...")
        await client.login()
        print("Logged in. Running probes...\n")
        await probe_client(client, "cloud", runner, rts_device_url=args.rts_device)


async def run_local(args: argparse.Namespace, runner: ProbeRunner):
    server_config = create_local_server_config(host=args.local_host)
    credentials = LocalTokenCredentials(token=args.local_token)

    trace_config = _build_trace_config()
    session = ClientSession(
        headers={"User-Agent": "python-overkiz-api"},
        trace_configs=[trace_config],
    )

    async with OverkizClient(
        server=server_config, credentials=credentials, session=session
    ) as client:
        print(f"\nConnecting to local API ({args.local_host})...")
        await client.login()
        print("Connected. Running probes...\n")
        await probe_client(client, "local", runner, rts_device_url=args.rts_device)


async def main():
    parser = argparse.ArgumentParser(
        description="Probe Overkiz endpoints for error handling",
        epilog="Credentials can also be set via env vars: OVERKIZ_SERVER, OVERKIZ_USERNAME, "
        "OVERKIZ_PASSWORD, OVERKIZ_LOCAL_HOST, OVERKIZ_LOCAL_TOKEN",
    )
    parser.add_argument(
        "--server", type=str, help="Cloud server key (e.g. somfy_europe)"
    )
    parser.add_argument("--username", type=str, help="Cloud username")
    parser.add_argument("--password", type=str, help="Cloud password")
    parser.add_argument("--local-host", type=str, help="Local gateway host:port")
    parser.add_argument("--local-token", type=str, help="Local API token")
    parser.add_argument(
        "--rts-device",
        type=str,
        help="RTS device URL to test commands on (e.g. rts://2025-8464-6867/16756006). "
        "Auto-detected from setup if not specified.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Only show the summary table, suppress HTTP traces",
    )
    args = parser.parse_args()

    # Fall back to env vars for credentials (avoids shell quoting issues with passwords)
    args.server = args.server or os.environ.get("OVERKIZ_SERVER")
    args.username = args.username or os.environ.get("OVERKIZ_USERNAME")
    args.password = args.password or os.environ.get("OVERKIZ_PASSWORD")
    args.local_host = args.local_host or os.environ.get("OVERKIZ_LOCAL_HOST")
    args.local_token = args.local_token or os.environ.get("OVERKIZ_LOCAL_TOKEN")
    args.rts_device = args.rts_device or os.environ.get("OVERKIZ_RTS_DEVICE")

    has_cloud = args.server and args.username and args.password
    has_local = args.local_host and args.local_token

    if not has_cloud and not has_local:
        parser.error(
            "Provide --server/--username/--password for cloud, "
            "and/or --local-host/--local-token for local."
        )

    runner = ProbeRunner(quiet=args.quiet)

    if has_cloud:
        try:
            await run_cloud(args, runner)
        except Exception:
            print(f"\nCloud session failed:\n{traceback.format_exc()}")

    if has_local:
        try:
            await run_local(args, runner)
        except Exception:
            print(f"\nLocal session failed:\n{traceback.format_exc()}")

    runner.print_report()
    sys.exit(0 if all(r.passed for r in runner.results) else 1)


if __name__ == "__main__":
    asyncio.run(main())
