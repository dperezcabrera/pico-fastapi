# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.html).

## [0.1.0] - 2025-11-02

### Added

* Initial public release of `pico-fastapi`.
* **`@controller`** decorator for class-based, dependency-injected API routers.
* Route decorators (`@get`, `@post`, `@put`, `@delete`, `@patch`, `@websocket`) for controller methods.
* **`PicoScopeMiddleware`** for automatic `request`, `session`, and `websocket` scope management, linking FastAPI's lifecycle to `pico-ioc`.
* **`FastApiAppFactory`** to provide a `FastAPI` instance as an injectable singleton.
* **`FastApiSettings`** dataclass for type-safe application configuration via `@configured`.
* **`FastApiConfigurer`** protocol for creating custom, prioritized setup hooks.
* Automatic FastAPI `lifespan` integration to manage container startup and shutdown (`cleanup_all_async`, `shutdown`).
* Custom exceptions (`InvalidConfigurerError`, `NoControllersFoundError`).

