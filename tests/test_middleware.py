"""Unit tests for pico_fastapi middleware."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pico_fastapi.middleware import (
    PicoScopeMiddleware,
    _cleanup_scope,
    _get_or_create_session_id,
)


class TestCleanupScope:
    """Tests for _cleanup_scope helper function."""

    def test_calls_cleanup_when_caches_exist(self):
        """Calls cleanup_scope when container has _caches."""
        container = MagicMock()
        container._caches = MagicMock()

        _cleanup_scope(container, "request", "req-123")

        container._caches.cleanup_scope.assert_called_once_with("request", "req-123")

    def test_no_error_when_caches_missing(self):
        """Does nothing when container has no _caches."""
        container = MagicMock(spec=[])  # No _caches attribute

        # Should not raise
        _cleanup_scope(container, "request", "req-123")


class TestGetOrCreateSessionId:
    """Tests for _get_or_create_session_id helper function."""

    def test_creates_new_session_id(self):
        """Creates new session ID when not present."""
        scope = {"session": {}}

        session_id = _get_or_create_session_id(scope)

        assert "pico_session_id" in scope["session"]
        assert session_id == scope["session"]["pico_session_id"]
        assert len(session_id) == 36  # UUID format

    def test_returns_existing_session_id(self):
        """Returns existing session ID when present."""
        existing_id = "existing-session-id"
        scope = {"session": {"pico_session_id": existing_id}}

        session_id = _get_or_create_session_id(scope)

        assert session_id == existing_id


class TestPicoScopeMiddleware:
    """Tests for PicoScopeMiddleware class."""

    @pytest.fixture
    def mock_container(self):
        """Create a mock container with scope context manager."""
        container = MagicMock()
        container.as_current.return_value.__enter__ = MagicMock()
        container.as_current.return_value.__exit__ = MagicMock()
        container.scope.return_value.__enter__ = MagicMock()
        container.scope.return_value.__exit__ = MagicMock()
        container._caches = MagicMock()
        return container

    @pytest.fixture
    def mock_app(self):
        """Create a mock ASGI app."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_http_request_creates_request_scope(self, mock_container, mock_app):
        """HTTP requests create a request scope."""
        middleware = PicoScopeMiddleware(mock_app, mock_container)
        scope = {"type": "http"}

        await middleware(scope, AsyncMock(), AsyncMock())

        mock_container.scope.assert_called()
        # First call should be with "request"
        call_args = mock_container.scope.call_args_list[0]
        assert call_args[0][0] == "request"

    @pytest.mark.asyncio
    async def test_http_request_with_session_creates_session_scope(self, mock_container, mock_app):
        """HTTP requests with session create both request and session scopes."""
        middleware = PicoScopeMiddleware(mock_app, mock_container)
        session = {}
        scope = {"type": "http", "session": session}

        await middleware(scope, AsyncMock(), AsyncMock())

        # Should have created both request and session scopes
        scope_calls = [call[0][0] for call in mock_container.scope.call_args_list]
        assert "request" in scope_calls
        assert "session" in scope_calls

    @pytest.mark.asyncio
    async def test_http_request_with_existing_session_id(self, mock_container, mock_app):
        """HTTP requests reuse existing session ID."""
        middleware = PicoScopeMiddleware(mock_app, mock_container)
        existing_session_id = "existing-session-123"
        session = {"pico_session_id": existing_session_id}
        scope = {"type": "http", "session": session}

        await middleware(scope, AsyncMock(), AsyncMock())

        # Find the session scope call
        for call in mock_container.scope.call_args_list:
            if call[0][0] == "session":
                assert call[0][1] == existing_session_id
                break

    @pytest.mark.asyncio
    async def test_http_request_generates_session_id_if_missing(self, mock_container, mock_app):
        """HTTP requests generate session ID if not present."""
        middleware = PicoScopeMiddleware(mock_app, mock_container)
        session = {}
        scope = {"type": "http", "session": session}

        await middleware(scope, AsyncMock(), AsyncMock())

        # Session should now have a pico_session_id
        assert "pico_session_id" in session
        assert len(session["pico_session_id"]) == 36  # UUID length

    @pytest.mark.asyncio
    async def test_websocket_creates_websocket_scope(self, mock_container, mock_app):
        """WebSocket connections create a websocket scope."""
        middleware = PicoScopeMiddleware(mock_app, mock_container)
        scope = {"type": "websocket"}

        await middleware(scope, AsyncMock(), AsyncMock())

        mock_container.scope.assert_called()
        call_args = mock_container.scope.call_args_list[0]
        assert call_args[0][0] == "websocket"

    @pytest.mark.asyncio
    async def test_other_scope_types_pass_through(self, mock_container, mock_app):
        """Non-http/websocket requests pass through without creating scopes."""
        middleware = PicoScopeMiddleware(mock_app, mock_container)
        scope = {"type": "lifespan"}

        await middleware(scope, AsyncMock(), AsyncMock())

        # Should still call as_current but not scope
        mock_container.as_current.assert_called_once()
        # The scope() shouldn't be called for lifespan
        mock_container.scope.assert_not_called()
        mock_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_scope_cleanup_on_completion(self, mock_container, mock_app):
        """Request scope is cleaned up after request completes."""
        middleware = PicoScopeMiddleware(mock_app, mock_container)
        scope = {"type": "http"}

        await middleware(scope, AsyncMock(), AsyncMock())

        mock_container._caches.cleanup_scope.assert_called()
        cleanup_call = mock_container._caches.cleanup_scope.call_args
        assert cleanup_call[0][0] == "request"

    @pytest.mark.asyncio
    async def test_websocket_scope_cleanup_on_completion(self, mock_container, mock_app):
        """WebSocket scope is cleaned up after connection closes."""
        middleware = PicoScopeMiddleware(mock_app, mock_container)
        scope = {"type": "websocket"}

        await middleware(scope, AsyncMock(), AsyncMock())

        mock_container._caches.cleanup_scope.assert_called()
        cleanup_call = mock_container._caches.cleanup_scope.call_args
        assert cleanup_call[0][0] == "websocket"

    @pytest.mark.asyncio
    async def test_cleanup_when_app_raises(self, mock_container):
        """Scope is cleaned up even when app raises exception."""
        async def failing_app(scope, receive, send):
            raise ValueError("App error")

        # Ensure context managers propagate exceptions (return False from __exit__)
        mock_container.as_current.return_value.__exit__ = MagicMock(return_value=False)
        mock_container.scope.return_value.__exit__ = MagicMock(return_value=False)

        middleware = PicoScopeMiddleware(failing_app, mock_container)
        scope = {"type": "http"}

        with pytest.raises(ValueError):
            await middleware(scope, AsyncMock(), AsyncMock())

        # Cleanup should still be called
        mock_container._caches.cleanup_scope.assert_called()

    @pytest.mark.asyncio
    async def test_no_cleanup_when_caches_missing(self, mock_app):
        """No error when container has no _caches attribute."""
        container = MagicMock()
        container.as_current.return_value.__enter__ = MagicMock()
        container.as_current.return_value.__exit__ = MagicMock()
        container.scope.return_value.__enter__ = MagicMock()
        container.scope.return_value.__exit__ = MagicMock()
        del container._caches

        middleware = PicoScopeMiddleware(mock_app, container)
        scope = {"type": "http"}

        # Should not raise
        await middleware(scope, AsyncMock(), AsyncMock())

    @pytest.mark.asyncio
    async def test_calls_app_with_scope_receive_send(self, mock_container, mock_app):
        """Middleware calls app with original scope, receive, send."""
        middleware = PicoScopeMiddleware(mock_app, mock_container)
        scope = {"type": "http"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        mock_app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_unique_request_ids_per_request(self, mock_container, mock_app):
        """Each HTTP request gets a unique request ID."""
        middleware = PicoScopeMiddleware(mock_app, mock_container)
        scope = {"type": "http"}

        await middleware(scope, AsyncMock(), AsyncMock())
        first_request_id = mock_container.scope.call_args_list[0][0][1]

        mock_container.reset_mock()
        await middleware(scope, AsyncMock(), AsyncMock())
        second_request_id = mock_container.scope.call_args_list[0][0][1]

        assert first_request_id != second_request_id
