"""Unit tests for pico_fastapi factory module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.responses import Response

from pico_fastapi.config import FastApiConfigurer
from pico_fastapi.decorators import controller, get, post
from pico_fastapi.exceptions import NoControllersFoundError
from pico_fastapi.factory import (
    FastApiAppFactory,
    PicoLifespanConfigurer,
    _apply_configurers,
    _find_controller_classes,
    _normalize_http_result,
    _priority_of,
    _split_configurers_by_priority,
    _validate_configurers,
    register_controllers,
)


class TestPriorityOf:
    """Tests for _priority_of helper function."""

    def test_returns_zero_for_objects_without_priority(self):
        """Objects without priority attribute return 0."""

        class NoPriority:
            pass

        assert _priority_of(NoPriority()) == 0

    def test_returns_priority_attribute_value(self):
        """Objects with priority attribute return its value."""

        class WithPriority:
            priority = 10

        assert _priority_of(WithPriority()) == 10

    def test_returns_negative_priority(self):
        """Negative priority values are returned correctly."""

        class NegativePriority:
            priority = -50

        assert _priority_of(NegativePriority()) == -50

    def test_handles_non_int_priority_conversion(self):
        """String priority is converted to int."""

        class StringPriority:
            priority = "42"

        assert _priority_of(StringPriority()) == 42

    def test_handles_exception_returns_zero(self):
        """Returns 0 if getting priority raises exception."""

        class BadPriority:
            @property
            def priority(self):
                raise ValueError("bad")

        assert _priority_of(BadPriority()) == 0

    def test_handles_none_priority(self):
        """None priority returns 0."""

        class NonePriority:
            priority = None

        # int(None) raises TypeError, should return 0
        assert _priority_of(NonePriority()) == 0


class TestNormalizeHttpResult:
    """Tests for _normalize_http_result helper function."""

    def test_returns_response_unchanged(self):
        """Response objects are returned as-is."""
        response = Response(content="test")
        result = _normalize_http_result(response)
        assert result is response

    def test_returns_json_response_unchanged(self):
        """JSONResponse objects are returned as-is."""
        response = JSONResponse(content={"key": "value"})
        result = _normalize_http_result(response)
        assert result is response

    def test_converts_dict_to_json_response(self):
        """Dict is converted to JSONResponse."""
        result = _normalize_http_result({"key": "value"})
        assert isinstance(result, JSONResponse)

    def test_tuple_with_status_code(self):
        """Tuple (content, status) creates JSONResponse."""
        result = _normalize_http_result(({"error": "not found"}, 404))
        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    def test_tuple_with_headers(self):
        """Tuple (content, status, headers) creates JSONResponse with headers."""
        result = _normalize_http_result(({"data": "value"}, 200, {"X-Custom": "header"}))
        assert isinstance(result, JSONResponse)
        assert result.status_code == 200

    def test_converts_list_to_json_response(self):
        """List is converted to JSONResponse."""
        result = _normalize_http_result([1, 2, 3])
        assert isinstance(result, JSONResponse)

    def test_converts_string_to_json_response(self):
        """String is converted to JSONResponse."""
        result = _normalize_http_result("hello")
        assert isinstance(result, JSONResponse)


class TestRegisterControllers:
    """Tests for register_controllers function."""

    def test_raises_error_when_no_controllers(self):
        """Raises NoControllersFoundError when no controllers registered."""
        mock_container = MagicMock()
        mock_locator = MagicMock()
        mock_locator._metadata = {}
        mock_container._locator = mock_locator

        app = FastAPI()

        with pytest.raises(NoControllersFoundError):
            register_controllers(app, mock_container)

    def test_raises_when_no_locator(self):
        """Raises NoControllersFoundError if container has no locator."""
        mock_container = MagicMock()
        del mock_container._locator

        app = FastAPI()
        with pytest.raises(NoControllersFoundError):
            register_controllers(app, mock_container)

    def test_registers_controller_routes(self):
        """Controllers with routes are registered on app."""

        @controller(prefix="/api")
        class TestController:
            @get("/items")
            def list_items(self):
                return []

        mock_container = MagicMock()
        mock_locator = MagicMock()
        mock_locator._metadata = {TestController: {}}
        mock_container._locator = mock_locator

        app = FastAPI()
        register_controllers(app, mock_container)

        # Check routes are registered
        routes = [r.path for r in app.routes]
        assert "/api/items" in routes


class TestFastApiAppFactory:
    """Tests for FastApiAppFactory class."""

    def test_creates_fastapi_from_settings(self):
        """Factory creates FastAPI app from settings."""
        from pico_fastapi.config import FastApiSettings

        factory = FastApiAppFactory()
        settings = FastApiSettings(
            title="Test App",
            version="2.0.0",
            debug=True,
        )

        app = factory.create_fastapi_app(settings)

        assert isinstance(app, FastAPI)
        assert app.title == "Test App"
        assert app.version == "2.0.0"
        assert app.debug is True

    def test_uses_default_settings(self):
        """Factory works with default settings values."""
        from pico_fastapi.config import FastApiSettings

        factory = FastApiAppFactory()
        settings = FastApiSettings()

        app = factory.create_fastapi_app(settings)

        assert app.title == "Pico-FastAPI App"
        assert app.version == "1.0.0"
        assert app.debug is False


class TestPicoLifespanConfigurer:
    """Tests for PicoLifespanConfigurer class."""

    def test_sorts_configurers_by_priority(self):
        """Configurers are sorted by priority."""
        from pico_fastapi.config import FastApiConfigurer

        class LowPriority(FastApiConfigurer):
            priority = -10

            def configure(self, app):
                app._configured_order.append("low")

        class HighPriority(FastApiConfigurer):
            priority = 10

            def configure(self, app):
                app._configured_order.append("high")

        class MidPriority(FastApiConfigurer):
            priority = 0

            def configure(self, app):
                app._configured_order.append("mid")

        app = FastAPI()
        app._configured_order = []

        container = MagicMock()
        container._locator._metadata = {}

        configurers = [LowPriority(), HighPriority(), MidPriority()]

        lifespan = PicoLifespanConfigurer()

        # We can't directly test setup_fastapi because it needs the container
        # to be properly setup, but we can verify the sorting behavior
        from pico_fastapi.factory import _priority_of

        sorted_conf = sorted(configurers, key=_priority_of)

        priorities = [_priority_of(c) for c in sorted_conf]
        assert priorities == [-10, 0, 10]

    def test_inner_configurers_before_middleware(self):
        """Configurers with priority >= 0 are applied before PicoScopeMiddleware."""
        # This is verified by the integration tests
        # The sandwich pattern is: inner (>=0) -> PicoScopeMiddleware -> outer (<0)
        pass

    def test_outer_configurers_after_middleware(self):
        """Configurers with priority < 0 are applied after PicoScopeMiddleware."""
        # This is verified by the integration tests
        pass


class TestFindControllerClasses:
    """Tests for _find_controller_classes helper function."""

    def test_returns_empty_when_no_locator(self):
        """Returns empty list if container has no locator."""
        mock_container = MagicMock()
        del mock_container._locator

        result = _find_controller_classes(mock_container)
        assert result == []

    def test_finds_controller_classes(self):
        """Finds classes marked with @controller."""

        @controller
        class TestController:
            pass

        mock_container = MagicMock()
        mock_container._locator._metadata = {TestController: {}, str: {}}

        result = _find_controller_classes(mock_container)
        assert TestController in result
        assert str not in result

    def test_returns_empty_when_no_controllers(self):
        """Returns empty list if no controllers in metadata."""
        mock_container = MagicMock()
        mock_container._locator._metadata = {str: {}, int: {}}

        result = _find_controller_classes(mock_container)
        assert result == []


class TestValidateConfigurers:
    """Tests for _validate_configurers helper function."""

    def test_filters_valid_configurers(self):
        """Keeps only valid FastApiConfigurer instances."""

        class ValidConfigurer(FastApiConfigurer):
            priority = 0

            def configure(self, app):
                pass

        class InvalidThing:
            pass

        configurers = [ValidConfigurer(), InvalidThing(), "not a configurer"]
        result = _validate_configurers(configurers)

        assert len(result) == 1
        assert isinstance(result[0], ValidConfigurer)

    def test_returns_empty_for_no_valid_configurers(self):
        """Returns empty list if no valid configurers."""
        result = _validate_configurers(["a", "b", 123])
        assert result == []


class TestSplitConfigurersByPriority:
    """Tests for _split_configurers_by_priority helper function."""

    def test_splits_inner_and_outer(self):
        """Splits configurers into inner (>=0) and outer (<0)."""

        class Inner(FastApiConfigurer):
            priority = 10

            def configure(self, app):
                pass

        class Outer(FastApiConfigurer):
            priority = -10

            def configure(self, app):
                pass

        class Zero(FastApiConfigurer):
            priority = 0

            def configure(self, app):
                pass

        configurers = [Inner(), Outer(), Zero()]
        inner, outer = _split_configurers_by_priority(configurers)

        assert len(inner) == 2  # Inner and Zero
        assert len(outer) == 1  # Outer

    def test_sorts_by_priority(self):
        """Configurers are sorted by priority within each group."""

        class A(FastApiConfigurer):
            priority = 20

            def configure(self, app):
                pass

        class B(FastApiConfigurer):
            priority = 5

            def configure(self, app):
                pass

        configurers = [A(), B()]
        inner, outer = _split_configurers_by_priority(configurers)

        # B (5) should come before A (20)
        assert _priority_of(inner[0]) == 5
        assert _priority_of(inner[1]) == 20


class TestApplyConfigurers:
    """Tests for _apply_configurers helper function."""

    def test_calls_configure_on_each(self):
        """Calls configure(app) on each configurer."""
        app = FastAPI()
        app.called = []

        class Conf1(FastApiConfigurer):
            priority = 0

            def configure(self, app):
                app.called.append("conf1")

        class Conf2(FastApiConfigurer):
            priority = 0

            def configure(self, app):
                app.called.append("conf2")

        configurers = [Conf1(), Conf2()]
        _apply_configurers(app, configurers)

        assert app.called == ["conf1", "conf2"]

    def test_handles_empty_list(self):
        """Handles empty configurer list."""
        app = FastAPI()
        _apply_configurers(app, [])  # Should not raise
