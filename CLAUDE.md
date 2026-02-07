Read and follow ./AGENTS.md for project conventions.

## Pico Ecosystem Context

pico-fastapi provides FastAPI integration for pico-ioc. It uses:
- `@component` from pico-ioc for controllers
- `@configured` for FastApiSettings
- `MethodInterceptor` is NOT used here (unlike pico-sqlalchemy/pico-pydantic)
- Auto-discovered via `pico_boot.modules` entry point

## Key Reminders

- pico-ioc dependency: `>= 2.2.0`
- **NEVER change `version_scheme`** in pyproject.toml. It MUST remain `"post-release"`. Changing it to `"guess-next-dev"` causes `.dev0` versions to leak to PyPI. This was already fixed once — do not revert it.
- requires-python >= 3.11
- Commit messages: one line only
- CI badge must point to `pico-fastapi` repo (not pico-ioc)
- Internal pico-ioc attributes: `_pico_meta`, `_pico_infra` (not dunder versions)
