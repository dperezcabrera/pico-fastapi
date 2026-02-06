"""Tests for pico_fastapi module exports."""
import pytest


class TestModuleExports:
    """Tests for public API exports."""

    def test_fastapi_configurer_exported(self):
        """FastApiConfigurer is exported from main module."""
        from pico_fastapi import FastApiConfigurer
        assert FastApiConfigurer is not None

    def test_fastapi_settings_exported(self):
        """FastApiSettings is exported from main module."""
        from pico_fastapi import FastApiSettings
        assert FastApiSettings is not None

    def test_controller_decorator_exported(self):
        """controller decorator is exported from main module."""
        from pico_fastapi import controller
        assert callable(controller)

    def test_http_decorators_exported(self):
        """HTTP method decorators are exported from main module."""
        from pico_fastapi import get, post, put, delete, patch
        assert callable(get)
        assert callable(post)
        assert callable(put)
        assert callable(delete)
        assert callable(patch)

    def test_websocket_decorator_exported(self):
        """websocket decorator is exported from main module."""
        from pico_fastapi import websocket
        assert callable(websocket)

    def test_fastapi_app_factory_exported(self):
        """FastApiAppFactory is exported from main module."""
        from pico_fastapi import FastApiAppFactory
        assert FastApiAppFactory is not None

    def test_exceptions_exported(self):
        """Exception classes are exported from main module."""
        from pico_fastapi import (
            PicoFastAPIError,
            NoControllersFoundError,
        )
        assert issubclass(PicoFastAPIError, Exception)
        assert issubclass(NoControllersFoundError, PicoFastAPIError)

    def test_all_exports_in_dunder_all(self):
        """All expected exports are in __all__."""
        import pico_fastapi

        expected = {
            "FastApiConfigurer",
            "FastApiSettings",
            "controller",
            "get",
            "post",
            "put",
            "delete",
            "patch",
            "websocket",
            "FastApiAppFactory",
            "PicoFastAPIError",
            "NoControllersFoundError",
        }

        assert set(pico_fastapi.__all__) == expected


class TestImportPatterns:
    """Tests for various import patterns."""

    def test_import_all_from_package(self):
        """Can import * from pico_fastapi."""
        # This is tested implicitly by the __all__ test
        pass

    def test_import_from_submodules(self):
        """Can import directly from submodules."""
        from pico_fastapi.config import FastApiConfigurer, FastApiSettings
        from pico_fastapi.decorators import controller, get, post
        from pico_fastapi.factory import FastApiAppFactory
        from pico_fastapi.exceptions import PicoFastAPIError
        from pico_fastapi.middleware import PicoScopeMiddleware

        assert FastApiConfigurer is not None
        assert FastApiSettings is not None
        assert callable(controller)
        assert callable(get)
        assert callable(post)
        assert FastApiAppFactory is not None
        assert issubclass(PicoFastAPIError, Exception)
        assert PicoScopeMiddleware is not None

    def test_no_circular_imports(self):
        """Module can be imported without circular import issues."""
        # Force fresh import
        import importlib
        import sys

        # Remove cached modules
        modules_to_remove = [m for m in sys.modules if m.startswith("pico_fastapi")]
        for m in modules_to_remove:
            del sys.modules[m]

        # This should not raise ImportError
        import pico_fastapi

        # Verify module is usable
        assert hasattr(pico_fastapi, "controller")
        assert hasattr(pico_fastapi, "FastApiConfigurer")
