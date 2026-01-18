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

## Tests and linting

```bash
uv run pytest
```

```bash
uv run prek run --all-files
```

## Project guidelines

- Use Python 3.10–3.13 features and type annotations.
- Keep absolute imports and avoid relative imports.
- Preserve existing comments and logging unless your change requires updates.
- Prefer small, focused changes and add tests when behavior changes.

## Submitting changes

1. Create a feature branch.
2. Run linting and tests.
3. Open a pull request with a clear description and context.
