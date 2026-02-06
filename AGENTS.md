# pico-fastapi

FastAPI integration for pico-ioc. Class-based controllers with DI, scope middleware, and configurer system.

## Commands

```bash
pip install -e ".[test]"          # Install in dev mode
pytest tests/ -v                  # Run tests
pytest --cov=pico_fastapi --cov-report=term-missing tests/  # Coverage
tox                               # Full matrix (3.11-3.14)
mkdocs serve -f mkdocs.yml        # Local docs
```

## Project Structure

```
src/pico_fastapi/
  __init__.py          # Public API exports
  decorators.py        # @controller, @get, @post, @put, @delete, @patch, @websocket
  middleware.py        # PicoScopeMiddleware - request/session/websocket scope management
  factory.py           # FastApiAppFactory, PicoLifespanConfigurer, register_controllers()
  config.py            # FastApiSettings, FastApiConfigurer protocol
  exceptions.py        # NoControllersFoundError, InvalidConfigurerError
```

## Key Concepts

- **`@controller(prefix="/api")`**: Class-based API router with DI. Methods decorated with `@get`, `@post`, etc.
- **`PicoScopeMiddleware`**: ASGI middleware managing `request`, `session`, `websocket` scopes via pico-ioc's ScopeManager
- **`FastApiConfigurer`**: Protocol for setup hooks. `priority >= 0` = inner (after scope middleware), `priority < 0` = outer (before). Sandwich pattern.
- **`FastApiAppFactory`**: Creates FastAPI app from `FastApiSettings`
- **`PicoLifespanConfigurer`**: Applies configurers, registers controllers, adds scope middleware during app lifespan
- **Controller discovery**: Via `container._locator._metadata` - finds classes with `_pico_meta` containing controller info

## Code Style

- Python 3.11+
- Async-first for all middleware and controller methods
- Use pico-ioc's `@component`, `@configured` decorators
- WebSocket parameter detected by type annotation (`ws: WebSocket`), not by name

## Testing

- pytest + pytest-asyncio (mode=strict)
- Mock pico-ioc container with `MagicMock` for unit tests
- `MagicMock.__exit__` must return `False` to propagate exceptions in context manager mocks
- Target: >95% coverage

## Boundaries

- Do not modify `_version.py`
- Controllers discovered from container metadata, not a global registry
- No direct dependency on pico-boot (uses entry point for auto-discovery)
