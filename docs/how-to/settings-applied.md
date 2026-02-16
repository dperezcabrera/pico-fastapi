# Apply FastAPI settings via dependency injection

This guide shows how to centralize and apply your FastAPI application settings (title, version, debug) using `FastApiSettings` and the pico-ioc container. Settings are automatically loaded from configuration sources and injected into the FastAPI app factory.

## What is this?

- **FastApiSettings**: A `@configured` dataclass that holds FastAPI metadata (title, version, debug). Automatically populated from configuration sources with the `fastapi` prefix.
- **FastApiConfigurer**: A protocol for pluggable components that configure the FastAPI app (add middleware, routers, event handlers). Multiple configurers run in priority order.
- **pico-ioc / pico-boot**: The DI container discovers and wires everything automatically.

This pattern keeps environment-specific values outside your application code and allows replacing them via configuration for tests, local runs, or production deployments.

## How do I use it?

### 1) Provide settings via configuration

Create a YAML file (or use environment variables / dict) with the `fastapi` prefix:

```yaml
# application.yaml
fastapi:
  title: My API
  version: 2.0.0
  debug: true
```

`FastApiSettings` is already defined by pico-fastapi — you do not need to redefine it. The container loads it automatically from your configuration source.

### 2) Bootstrap the application

Use `pico-boot` to initialize the container and retrieve the configured FastAPI app:

```python
from fastapi import FastAPI
from pico_boot import init
from pico_ioc import configuration, YamlTreeSource

config = configuration(YamlTreeSource("application.yaml"))
container = init(modules=["myapp"], config=config)
app = container.get(FastAPI)

# app.title == "My API"
# app.version == "2.0.0"
# app.debug == True
```

The `FastApiAppFactory` (provided by pico-fastapi) reads `FastApiSettings` and creates the `FastAPI` instance as a singleton.

### 3) Add custom configurers (optional)

If you need to apply additional configuration (middleware, routers), implement `FastApiConfigurer`:

```python
from pico_ioc import component
from pico_fastapi import FastApiConfigurer
from fastapi import FastAPI

@component
class CORSConfigurer(FastApiConfigurer):
    priority = -100  # Outer middleware (before PicoScopeMiddleware)

    def configure(self, app: FastAPI) -> None:
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

Configurers decorated with `@component` are automatically discovered and executed in priority order.

### 4) Verify the settings (example test)

```python
from fastapi import FastAPI
from pico_boot import init
from pico_ioc import configuration, DictTreeSource

def test_settings_applied():
    config = configuration(DictTreeSource({
        "fastapi": {
            "title": "Integration Test API",
            "version": "9.9.9",
            "debug": True,
        }
    }))
    container = init(modules=["myapp"], config=config)
    app = container.get(FastAPI)

    assert app.title == "Integration Test API"
    assert app.version == "9.9.9"
    assert app.debug is True
```

## Notes and tips

- **Apply settings early**: Debug mode affects exception handling and error pages; settings are applied during app creation, before any routers or middleware.
- **Priority ordering**: Use the `priority` attribute on configurers to control execution order. Negative = outer middleware, non-negative = inner middleware.
- **Testability**: Pass different configuration sources (e.g., `DictTreeSource`) to provide test-specific settings without changing application code.