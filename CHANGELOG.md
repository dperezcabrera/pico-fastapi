# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.html).

---

## v0.2.2 — Internal Quality (2026-02-06)

### Changed
- **Error Handling**: Replaced `InvalidConfigurerError` exception with a `logger.warning()` — invalid configurers are now logged and discarded instead of raising.
- **Logging**: Added `logging` to `factory.py` for configurer validation and WebSocket parameter detection.

### Removed
- **`InvalidConfigurerError`**: Removed exception class, its export from `__init__.py`, and all related tests.

### Fixed
- **Code Quality**: Changed bare `except:` to `except Exception:` in test conftest.

---

## v0.2.1 — Fixes & Quality (2026-02-05)

### Fixed
- Fixed CI badge in README pointing to pico-ioc instead of pico-fastapi.
- Fixed all references from `pico-stack` to `pico-boot` in CHANGELOG and release notes.
- Fixed 5 broken unit tests against current pico-ioc attribute names (`_pico_meta`, `_pico_infra`).
- Fixed middleware test mock not propagating exceptions correctly.
- Fixed factory test expecting silent return instead of `NoControllersFoundError`.
- Removed redundant `pip install pico-ioc fastapi` from README (already dependencies).

### Changed
- Bumped `pico-ioc` dependency from `>= 2.1.3` to `>= 2.2.0`.
- Dropped Python 3.10 from CI matrix, tox and Makefile (requires-python is `>=3.11`).
- Changed `version_scheme` from `post-release` to `guess-next-dev` for clean release versions.

---

## v0.2.0 — Ecosystem Integration (2025-11-25)

### 🔌 New
- Added native `pico-boot` auto-discovery using the `pico_boot.modules` entry point.
- `pico-fastapi` is now automatically detected and loaded when initializing applications with `pico-boot`.

### 🧱 No Behavioral Changes
- No updates to middleware behavior.
- No DI or request lifecycle changes.
- No breaking changes.

This release focuses exclusively on ecosystem alignment and improving the developer experience when bootstrapping applications with `pico-boot`.

---

## [0.1.2] - 2025-11-18

### Fixed
- **Middleware Ordering:** Fixed a critical issue where `PicoScopeMiddleware` was always added last (outermost), preventing inner middlewares (like Authentication) from accessing the IoC container.
- **Architecture:** Implemented a "Sandwich" strategy for `FastApiConfigurer`. Configurers with negative priority (`priority < 0`) now wrap the scope middleware (e.g., Session, CORS), while configurers with positive priority (`priority >= 0`) run inside the scope (e.g., Auth, Business Logic).

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

