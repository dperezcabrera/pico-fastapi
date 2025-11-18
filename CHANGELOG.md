# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.html).

---

## [0.1.1] - 2025-11-18

### Fixed
- **Critical:** Fixed a memory leak in `PicoScopeMiddleware`. Request and WebSocket scopes were not being explicitly cleaned up after connection closure, leading to unbounded memory usage (aligned with `pico-ioc` v2.1.3 breaking changes).
- Fixed WebSocket argument injection mechanism. Previously, the controller method argument *had* to be named `websocket`. It is now detected dynamically by type annotation (`websocket: WebSocket`), allowing any argument name (e.g., `ws: WebSocket`).

### Changed
- **Architecture:** Removed the global `CONTROLLERS` set used for route registration. Controllers are now discovered by inspecting the `pico-ioc` container's metadata directly. This fixes state pollution issues during testing and ensures a single source of truth.
- Updated dependency requirement to `pico-ioc>=2.1.3`.

---

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

