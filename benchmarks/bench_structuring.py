"""Benchmark: measure time for structuring API responses.

Run with: python benchmarks/bench_structuring.py

Baseline (before optimization, with recursive decamelize pre-pass):
  TOTAL (sum of averages): ~18.20 ms

After optimization (cattrs rename hooks, single-pass):
  TOTAL (sum of averages): ~9.84 ms  (~46% faster)
"""
# ruff: noqa: T201, D103

from __future__ import annotations

import json
import time
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "setup"
DEVICES_FILE = Path(__file__).resolve().parent.parent / "tests" / "devices.json"


def load_fixtures() -> list[tuple[str, dict]]:
    """Load all setup fixture files as raw dicts (camelCase keys from API)."""
    fixtures = []
    for f in sorted(FIXTURES_DIR.glob("*.json")):
        with f.open() as fh:
            fixtures.append((f.name, json.load(fh)))
    return fixtures


def load_devices_fixture() -> list[dict]:
    """Load the devices.json fixture."""
    with DEVICES_FILE.open() as fh:
        return json.load(fh)


def bench_structure(iterations: int = 50) -> dict[str, float]:
    """Benchmark structure_response on all fixtures."""
    from pyoverkiz.converter import structure_response
    from pyoverkiz.models import Device, Setup

    fixtures = load_fixtures()
    devices_data = load_devices_fixture()

    results: dict[str, float] = {}

    for name, data in fixtures:
        start = time.perf_counter()
        for _ in range(iterations):
            structure_response(data, Setup)
        elapsed = time.perf_counter() - start
        results[f"Setup({name})"] = elapsed / iterations

    start = time.perf_counter()
    for _ in range(iterations):
        structure_response(devices_data, list[Device])
    elapsed = time.perf_counter() - start
    results["list[Device](devices.json)"] = elapsed / iterations

    return results


def main() -> None:
    print("Benchmarking structure_response (avg per call)...")
    print("=" * 70)

    results = bench_structure()

    for name, avg_time in sorted(results.items(), key=lambda x: -x[1]):
        print(f"  {name:<50} {avg_time * 1000:8.2f} ms")

    total = sum(results.values())
    print(f"\n  {'TOTAL (sum of averages)':<50} {total * 1000:8.2f} ms")
    print("=" * 70)


if __name__ == "__main__":
    main()
