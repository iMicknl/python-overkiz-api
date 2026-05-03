# Contribute

Thanks for contributing to pyOverkiz! This project powers production integrations and values careful changes, clear tests, and thoughtful documentation.

## Development setup

```bash
uv sync
```

Install git hooks:

```bash
uv run prek install
```

## Run the docs locally

```bash
uv run mkdocs serve
```

Docs will be available at http://localhost:8000.

```bash
uv run mkdocs build
```

## Tests and linting

```bash
uv run pytest
```

```bash
uv run prek run --all-files
```

## Enum generation

Several enum files in `pyoverkiz/enums/` are **auto-generated** — do not edit them manually. The generator script (`utils/generate_enums.py`) fetches reference data from the Overkiz API and merges it with commands/state values found in local fixture files.

Generated files: `protocol.py`, `ui.py`, `ui_profile.py`, `command.py`.

### Running the generator

Run the script with credentials inline:

```bash
OVERKIZ_USERNAME="your@email.com" OVERKIZ_PASSWORD="your-password" uv run utils/generate_enums.py
```

By default the script connects to `somfy_europe`. Pass `--server` to use a different one (e.g. `atlantic_cozytouch`, `thermor_cozytouch`):

```bash
uv run utils/generate_enums.py --server atlantic_cozytouch
```

The generated files are automatically formatted with `ruff`.

Some protocols and widgets only exist on specific servers. These are hardcoded at the top of the script (`ADDITIONAL_PROTOCOLS`, `ADDITIONAL_WIDGETS`) and merged in automatically.

After regenerating, run linting and tests:

```bash
uv run prek run --all-files
uv run pytest
```

## Project guidelines

- Use Python 3.12+ features and type annotations.
- Keep absolute imports and avoid relative imports.
- Preserve existing comments and logging unless your change requires updates.
- Prefer small, focused changes and add tests when behavior changes.

## Submitting changes

1. Fork the repository and create a new feature branch for your changes.
2. Ensure all linting and tests pass locally before submitting.
3. Open a pull request with a clear description and context.
