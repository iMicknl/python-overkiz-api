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

## Project guidelines

- Use Python 3.10+ features and type annotations.
- Keep absolute imports and avoid relative imports.
- Preserve existing comments and logging unless your change requires updates.
- Prefer small, focused changes and add tests when behavior changes.

## Submitting changes

1. Fork the repository and create a new feature branch for your changes.
2. Ensure all linting and tests pass locally before submitting.
3. Open a pull request with a clear description and context.
