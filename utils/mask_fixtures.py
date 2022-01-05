from __future__ import annotations

import glob
import json
import os
import re
from typing import Any


def obfuscate_id(id: str | None) -> str:
    return re.sub(r"(SETUP)?\d+-", "1234-", str(id))


def obfuscate_email(email: str | None) -> str:
    return re.sub(r"(.).*@.*(.\..*)", r"\1****@****\2", str(email))


def mask(input: str | None) -> str:
    return re.sub(r"[a-zA-Z0-9_.-]+", "*", str(input))


def func1(data: Any) -> Any:

    mask_next_value = False

    for key, value in data.items():
        # print(str(key) + '->' + str(value))

        if key in ["gatewayId", "id", "deviceURL"]:
            data[key] = obfuscate_id(value)

        if key in [
            "label",
            "city",
            "country",
            "postalCode",
            "addressLine1",
            "addressLine2",
            "longitude",
            "latitude",
        ]:
            data[key] = mask(value)

        if value in ["core:NameState", "homekit:SetupCode", "homekit:SetupPayload"]:
            mask_next_value = True

        if mask_next_value and key == "value":
            data[key] = mask(value)
            mask_next_value = False

        # Mask homekit:SetupCode and homekit:SetupPayload
        if isinstance(value, dict):
            func1(value)
        elif isinstance(value, list):
            for val in value:
                if isinstance(val, str):
                    pass
                elif isinstance(val, list):
                    pass
                else:
                    func1(val)

    return data


# only process .JSON files in folder.
for filename in glob.glob(os.path.join("tests/fixtures/setup", "*.json")):
    with open(filename, encoding="utf-8") as input_file:

        print(f"Masking {filename}")

        try:
            file = json.loads(input_file.read())
            output = func1(file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Error while masking: {filename}")
            print(exception)
            continue

        with open(filename, encoding="utf-8", mode="w") as output_file:
            json.dump(output, output_file, ensure_ascii=False, indent=4)
