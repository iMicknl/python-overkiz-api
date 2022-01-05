from __future__ import annotations
from collections import abc

import re
import json
import os
import glob
import humps

# list_not_to_mask = ["id"]


def obfuscate_id(id: str | None) -> str:
    return re.sub(r"(SETUP)?\d+-", "1234-", str(id))


def obfuscate_email(email: str | None) -> str:
    return re.sub(r"(.).*@.*(.\..*)", r"\1****@****\2", str(email))


def mask(input: str | None) -> str:
    return re.sub(r"[a-zA-Z0-9_.-]+", "*", str(input))


def func1(data):

    mask_next_value = False

    for key, value in data.items():
        # print(str(key) + '->' + str(value))

        if key == "deviceurl":
            key = "deviceURL"

        if key == "placeoid":
            key = "placeOID"

        if key in ["gateway_id", "gatewayId", "id", "device_url", "deviceurl", "deviceURL"]:
            data[key] = obfuscate_id(value)

        if key in ["label", "city", "country", "postal_code", "postalCode", "address_line1", "addressLine1", "address_line2", "addressLine2", "longitude", "latitude"]:
            data[key] = mask(value)

        if value in ["core:NameState", "homekit:SetupCode", "homekit:SetupPayload"]:
            mask_next_value = True

        if mask_next_value and key == "value":
            data[key] = mask(value)
            mask_next_value = False

        # Mask homekit:SetupCode and homekit:SetupPayload
        if type(value) == dict:
            func1(value)
        elif type(value) == list:
            for val in value:
                if type(val) == str:
                    pass
                elif type(val) == list:
                    pass
                else:
                    func1(val)

    return data


list_not_to_mask = []


# only process .JSON files in folder.
for filename in glob.glob(os.path.join("tests/fixtures/setup", '*.json')):
    with open(filename, encoding='utf-8', mode='r') as input_file:

        print(f"Masking {filename}")

        try:
            input = json.loads(input_file.read())
            input = humps.camelize(input)
            output = func1(input)
        except Exception as exception:
            print(f"Error while masking: {filename}")
            print(exception)
            continue

        with open(filename, encoding='utf-8', mode='w') as output_file:
            json.dump(output, output_file, ensure_ascii=False, indent=4)
