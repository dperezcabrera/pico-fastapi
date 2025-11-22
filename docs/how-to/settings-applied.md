# Apply FastAPI settings via dependency injection

This guide shows how to centralize and apply your FastAPI application settings (title, version, debug) using a configurable protocol and an injectable settings dataclass. It uses a dependency injection (DI) container (pico_ioc) to wire the settings into a configurer that updates the FastAPI app instance. A test verifies the app title is "Integration Test API", version is "9.9.9", and debug mode is enabled.

## What is this?

- FastApiSettings: A simple dataclass that holds FastAPI metadata:
  - title: Application title
  - version: Semantic version string
  - debug: Boolean flag for Starlette/FastAPI debug mode

- FastApiConfigurer: A protocol you implement to configure a FastAPI app. It exposes:
  - priority(): Returns a number used to order the execution of multiple configurers.
  - configure(app): Applies configuration to the given FastAPI app instance.

- pico_ioc: A lightweight DI container that can:
  - Provide FastApiSettings to your configurer based on type annotation.
  - Resolve and execute all registered FastApiConfigurer implementations in a deterministic order.

This pattern keeps environment-specific values (e.g., title, version, debug) outside your application wiring and allows replacing them via DI for tests, local runs, or production deployments.

## How do I use it?

### 1) Define your settings

Create an instance of FastApiSettings. In practice, you can construct this from environment variables or configuration files.

```python
from dataclasses import dataclass

@dataclass
class FastApiSettings:
    title: str
    version: str
    debug: bool = False

# Example values (used by the test)
settings = FastApiSettings(
    title="Integration Test API",
    version="9.9.9",
    debug=True,
)
```

### 2) Implement a FastApiConfigurer

Implement the protocol to apply the injected settings to the app. The DI container will inject FastApiSettings into the constructor.

```python
from fastapi import FastAPI

class FastApiConfigurer:
    def priority(self) -> int:
        ...

    def configure(self, app: FastAPI) -> None:
        ...

class AppSettingsConfigurer(FastApiConfigurer):
    def __init__(self, settings: FastApiSettings) -> None:
        self._settings = settings

    def priority(self) -> int:
        # Lower numbers run earlier; pick any scheme that suits your boot order.
        return 100

    def configure(self, app: FastAPI) -> None:
        # Apply metadata and debug flags to the app
        app.title = self._settings.title
        app.version = self._settings.version
        app.debug = self._settings.debug
```

### 3) Register settings and configurer in pico_ioc

Wire the settings and configurer into the DI container. The exact container API may differ based on your setup; conceptually you:

- Register the FastApiSettings instance.
- Register the AppSettingsConfigurer so it can be resolved as a FastApiConfigurer.

```python
# Pseudocode: adapt to your pico_ioc setup
from pico_ioc import Container

ioc = Container()

# Provide the settings instance
ioc.register_instance(FastApiSettings, settings)

# Register the configurer; the container will inject FastApiSettings
ioc.register(AppSettingsConfigurer, as_type=FastApiConfigurer)
```

### 4) Build your FastAPI app and apply configurers

Create the app and execute all configurers in order. This should happen as early as possible in your application bootstrap.

```python
from fastapi import FastAPI

app = FastAPI()

# Resolve and run all configurers
configurers = ioc.resolve_all(FastApiConfigurer)
for cfg in sorted(configurers, key=lambda c: c.priority()):
    cfg.configure(app)
```

At this point, the app has the configured title, version, and debug mode.

### 5) Verify the settings (example test)

A basic test ensures the configuration has been applied:

```python
def test_settings_title_version_debug(app: FastAPI) -> None:
    assert app.title == "Integration Test API"
    assert app.version == "9.9.9"
    assert app.debug is True
```

## Notes and tips

- Apply settings early: Debug mode affects exception handling and error pages; set it before mounting routers or starting the server.
- Priority ordering: Use priority() to control configurer execution when you have several app-wide configuration steps (e.g., CORS, middleware, routes).
- Extensible settings: You can add fields to FastApiSettings (e.g., OpenAPI URL, docs URL) and extend your configurer to apply them.
- Testability: Provide different FastApiSettings instances (e.g., via pico_ioc) for tests or environments without changing your application code.