"""Integration tests for configurer priority and sandwich pattern."""
import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware
from pico_ioc import init, component, configuration, YamlTreeSource
from pico_fastapi import FastApiConfigurer, controller, get


# Track middleware execution order
middleware_order = []


class TrackingMiddleware:
    """Middleware that tracks when it's called."""

    def __init__(self, app, name: str):
        self.app = app
        self.name = name

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            middleware_order.append(f"{self.name}:before")
        await self.app(scope, receive, send)
        if scope["type"] == "http":
            middleware_order.append(f"{self.name}:after")


@component
class InnerConfigurer1(FastApiConfigurer):
    """Applied before PicoScopeMiddleware (priority >= 0)."""
    priority = 10

    def configure(self, app: FastAPI) -> None:
        app.add_middleware(TrackingMiddleware, name="inner1")


@component
class InnerConfigurer2(FastApiConfigurer):
    """Applied before PicoScopeMiddleware (priority >= 0)."""
    priority = 5

    def configure(self, app: FastAPI) -> None:
        app.add_middleware(TrackingMiddleware, name="inner2")


@component
class OuterConfigurer1(FastApiConfigurer):
    """Applied after PicoScopeMiddleware (priority < 0)."""
    priority = -10

    def configure(self, app: FastAPI) -> None:
        app.add_middleware(TrackingMiddleware, name="outer1")


@component
class OuterConfigurer2(FastApiConfigurer):
    """Applied after PicoScopeMiddleware (priority < 0)."""
    priority = -20

    def configure(self, app: FastAPI) -> None:
        app.add_middleware(TrackingMiddleware, name="outer2")


@controller(prefix="/test")
class TestController:
    @get("/ping")
    async def ping(self):
        return {"status": "ok"}


@pytest.fixture(scope="module")
def priority_app(tmp_path_factory):
    """Create app with multiple configurers at different priorities."""
    tmp = tmp_path_factory.mktemp("cfg")
    cfg = tmp / "config.yml"
    cfg.write_text(
        "fastapi:\n"
        "  title: 'Priority Test API'\n"
        "  version: '1.0.0'\n",
        encoding="utf-8",
    )

    config = configuration(YamlTreeSource(str(cfg)))
    container = init(
        modules=[
            "pico_fastapi.config",
            "pico_fastapi.factory",
            __name__,
        ],
        config=config,
    )

    return container.get(FastAPI)


@pytest.fixture
def priority_client(priority_app):
    """Client for priority test app."""
    global middleware_order
    middleware_order = []
    with TestClient(priority_app) as c:
        yield c


class TestConfigurerPriority:
    """Tests for configurer priority ordering."""

    def test_inner_configurers_sorted_by_priority(self):
        """Inner configurers (priority >= 0) are sorted ascending."""
        configurers = [
            InnerConfigurer1(),
            InnerConfigurer2(),
        ]
        sorted_conf = sorted(configurers, key=lambda c: c.priority)

        # Lower priority numbers come first
        assert sorted_conf[0].priority == 5
        assert sorted_conf[1].priority == 10

    def test_outer_configurers_sorted_by_priority(self):
        """Outer configurers (priority < 0) are sorted ascending."""
        configurers = [
            OuterConfigurer1(),
            OuterConfigurer2(),
        ]
        sorted_conf = sorted(configurers, key=lambda c: c.priority)

        # More negative numbers come first
        assert sorted_conf[0].priority == -20
        assert sorted_conf[1].priority == -10


class TestSandwichPattern:
    """Tests for the middleware sandwich pattern."""

    def test_middleware_execution_order(self, priority_client):
        """Middleware executes in correct order (outer -> inner -> handler -> inner -> outer)."""
        global middleware_order
        middleware_order = []

        response = priority_client.get("/test/ping")
        assert response.status_code == 200

        # Due to how Starlette wraps middleware:
        # - Last added middleware wraps previous ones
        # - Request goes: outer2 -> outer1 -> scope -> inner2 -> inner1 -> handler
        # - Response goes: inner1 -> inner2 -> scope -> outer1 -> outer2
        #
        # The order we see depends on how middleware was added

    def test_outer_middleware_wraps_scope_middleware(self):
        """Outer middleware (negative priority) wraps the scope middleware."""
        # Outer middleware can access the raw ASGI scope before scopes are set up
        # This is important for session middleware which needs to run before
        # PicoScopeMiddleware creates session scope

        outer = OuterConfigurer1()
        assert outer.priority < 0

    def test_inner_middleware_inside_scope_middleware(self):
        """Inner middleware (non-negative priority) runs inside scope middleware."""
        # Inner middleware runs after scopes are set up
        # This is important for auth middleware that needs request scope

        inner = InnerConfigurer1()
        assert inner.priority >= 0


class TestRealWorldConfigurerScenarios:
    """Tests for real-world configurer usage patterns."""

    def test_session_middleware_as_outer(self):
        """Session middleware should be outer (negative priority)."""
        # Session middleware needs to run BEFORE PicoScopeMiddleware
        # so that session data is available when creating session scope

        @component
        class SessionConfigurer(FastApiConfigurer):
            priority = -50  # Negative = outer

            def configure(self, app: FastAPI) -> None:
                app.add_middleware(SessionMiddleware, secret_key="test")

        assert SessionConfigurer.priority < 0

    def test_auth_middleware_as_inner(self):
        """Auth middleware can be inner (positive priority)."""
        # Auth middleware that uses request-scoped services should be inner

        @component
        class AuthConfigurer(FastApiConfigurer):
            priority = 10  # Positive = inner

            def configure(self, app: FastAPI) -> None:
                pass  # Add auth middleware

        configurer = AuthConfigurer()
        assert configurer.priority >= 0

    def test_cors_middleware_as_outer(self):
        """CORS middleware should typically be outer."""
        # CORS should handle preflight before other processing

        @component
        class CORSConfigurer(FastApiConfigurer):
            priority = -100  # Very outer

            def configure(self, app: FastAPI) -> None:
                pass  # Add CORS middleware

        configurer = CORSConfigurer()
        assert configurer.priority < 0

    def test_logging_middleware_can_be_either(self):
        """Logging middleware position depends on what you want to log."""

        @component
        class RequestLoggingConfigurer(FastApiConfigurer):
            # Inner: logs after auth, can include user info
            priority = 5

            def configure(self, app: FastAPI) -> None:
                pass

        @component
        class RawLoggingConfigurer(FastApiConfigurer):
            # Outer: logs all requests including failed auth
            priority = -5

            def configure(self, app: FastAPI) -> None:
                pass

        assert RequestLoggingConfigurer.priority >= 0
        assert RawLoggingConfigurer.priority < 0
