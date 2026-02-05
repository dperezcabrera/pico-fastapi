"""Unit tests for pico_fastapi config module."""
import pytest
from dataclasses import asdict
from fastapi import FastAPI
from pico_fastapi.config import FastApiConfigurer, FastApiSettings


class TestFastApiSettings:
    """Tests for FastApiSettings dataclass."""

    def test_default_values(self):
        """Settings has sensible defaults."""
        settings = FastApiSettings()

        assert settings.title == "Pico-FastAPI App"
        assert settings.version == "1.0.0"
        assert settings.debug is False

    def test_custom_values(self):
        """Settings accepts custom values."""
        settings = FastApiSettings(
            title="My API",
            version="2.5.0",
            debug=True,
        )

        assert settings.title == "My API"
        assert settings.version == "2.5.0"
        assert settings.debug is True

    def test_is_dataclass(self):
        """FastApiSettings is a dataclass."""
        settings = FastApiSettings()
        assert asdict(settings) == {
            "title": "Pico-FastAPI App",
            "version": "1.0.0",
            "debug": False,
        }

    def test_can_create_fastapi_app(self):
        """Settings can be used to create FastAPI app."""
        settings = FastApiSettings(
            title="Test API",
            version="3.0.0",
            debug=True,
        )

        app = FastAPI(**asdict(settings))

        assert app.title == "Test API"
        assert app.version == "3.0.0"
        assert app.debug is True

    def test_has_configured_decorator(self):
        """FastApiSettings is marked with @configured."""
        assert getattr(FastApiSettings, "_pico_infra", None) == "configured"
        meta = getattr(FastApiSettings, "_pico_meta", {})
        assert "configured" in meta


class TestFastApiConfigurer:
    """Tests for FastApiConfigurer protocol."""

    def test_is_runtime_checkable_protocol(self):
        """FastApiConfigurer is a runtime checkable protocol."""
        from typing import runtime_checkable, Protocol

        assert hasattr(FastApiConfigurer, "__protocol_attrs__")

    def test_default_priority_is_zero(self):
        """Default priority property returns 0."""
        # Create a concrete implementation
        class MyConfigurer(FastApiConfigurer):
            def configure(self, app: FastAPI) -> None:
                pass

        configurer = MyConfigurer()
        assert configurer.priority == 0

    def test_instance_check_with_configure_method(self):
        """Objects with configure method pass isinstance check."""
        class ValidConfigurer:
            priority = 5

            def configure(self, app: FastAPI) -> None:
                pass

        assert isinstance(ValidConfigurer(), FastApiConfigurer)

    def test_instance_check_fails_without_configure(self):
        """Objects without configure method fail isinstance check."""
        class InvalidConfigurer:
            priority = 5

        assert not isinstance(InvalidConfigurer(), FastApiConfigurer)

    def test_custom_priority(self):
        """Configurers can define custom priority."""
        class HighPriorityConfigurer(FastApiConfigurer):
            priority = 100

            def configure(self, app: FastAPI) -> None:
                pass

        configurer = HighPriorityConfigurer()
        assert configurer.priority == 100

    def test_negative_priority_for_outer_middleware(self):
        """Negative priority places configurer outside scope middleware."""
        class OuterConfigurer(FastApiConfigurer):
            priority = -10

            def configure(self, app: FastAPI) -> None:
                pass

        configurer = OuterConfigurer()
        assert configurer.priority < 0


class TestConfigurerOrdering:
    """Tests for configurer priority ordering behavior."""

    def test_sorting_by_priority(self):
        """Configurers can be sorted by priority."""
        class LowPriority:
            priority = -50
            name = "low"

        class MidPriority:
            priority = 0
            name = "mid"

        class HighPriority:
            priority = 50
            name = "high"

        configurers = [MidPriority(), LowPriority(), HighPriority()]
        sorted_configurers = sorted(configurers, key=lambda c: c.priority)

        names = [c.name for c in sorted_configurers]
        assert names == ["low", "mid", "high"]

    def test_inner_outer_separation(self):
        """Configurers can be separated into inner and outer groups."""
        class Outer1:
            priority = -50

        class Inner1:
            priority = 10

        class Inner2:
            priority = 0

        class Outer2:
            priority = -10

        configurers = [Outer1(), Inner1(), Inner2(), Outer2()]

        inner = [c for c in configurers if c.priority >= 0]
        outer = [c for c in configurers if c.priority < 0]

        assert len(inner) == 2
        assert len(outer) == 2

    def test_sandwich_pattern_order(self):
        """Sandwich pattern: inner -> middleware -> outer."""
        class SessionMiddleware:  # Outer, priority -50
            priority = -50
            name = "session"

        class AuthMiddleware:  # Inner, priority 10
            priority = 10
            name = "auth"

        class CORSMiddleware:  # Outer, priority -10
            priority = -10
            name = "cors"

        configurers = [SessionMiddleware(), AuthMiddleware(), CORSMiddleware()]
        sorted_all = sorted(configurers, key=lambda c: c.priority)

        inner = [c for c in sorted_all if c.priority >= 0]
        outer = [c for c in sorted_all if c.priority < 0]

        # Inner middlewares go first (applied before scope middleware)
        assert [c.name for c in inner] == ["auth"]
        # Outer middlewares go after scope middleware
        assert [c.name for c in outer] == ["session", "cors"]
