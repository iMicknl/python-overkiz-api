"""Simple helper script to mask sensitive fields in JSON fixtures."""

# ruff: noqa: T201
# Utility scripts can use print for CLI output

from __future__ import annotations

import json
from pathlib import Path

from pyoverkiz.obfuscate import obfuscate_sensitive_data

# only process .JSON files in folder.
for filepath in Path("tests/fixtures/setup").glob("*.json"):
    with filepath.open(encoding="utf-8") as input_file:
        print(f"Masking {filepath}")

        try:
            file = json.loads(input_file.read())
            output = obfuscate_sensitive_data(file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Error while masking: {filepath}")
            print(exception)
            continue

        with filepath.open(encoding="utf-8", mode="w") as output_file:
            json.dump(output, output_file, ensure_ascii=False, indent=4)
