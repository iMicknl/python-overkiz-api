from __future__ import annotations

import glob
import json
import os

from pyoverkiz.utils import mask_json

# only process .JSON files in folder.
for filename in glob.glob(os.path.join("tests/fixtures/setup", "*.json")):
    with open(filename, encoding="utf-8") as input_file:

        print(f"Masking {filename}")

        try:
            file = json.loads(input_file.read())
            output = mask_json(file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Error while masking: {filename}")
            print(exception)
            continue

        with open(filename, encoding="utf-8", mode="w") as output_file:
            json.dump(output, output_file, ensure_ascii=False, indent=4)
