import uuid
from pico_ioc import PicoContainer


def _cleanup_scope(container: PicoContainer, scope_name: str, scope_id: str) -> None:
    """Clean up a scope if the container has caches."""
    if hasattr(container, "_caches"):
        container._caches.cleanup_scope(scope_name, scope_id)


def _get_or_create_session_id(scope: dict) -> str:
    """Get existing session ID or create a new one."""
    session = scope["session"]
    if "pico_session_id" not in session:
        session["pico_session_id"] = str(uuid.uuid4())
    return session["pico_session_id"]


class PicoScopeMiddleware:
    def __init__(self, app, container: PicoContainer):
        self.app = app
        self.container = container

    async def __call__(self, scope, receive, send):
        with self.container.as_current():
            scope_type = scope["type"]

            if scope_type == "http":
                await self._handle_http(scope, receive, send)
            elif scope_type == "websocket":
                await self._handle_websocket(scope, receive, send)
            else:
                await self.app(scope, receive, send)

    async def _handle_http(self, scope, receive, send):
        """Handle HTTP request with request and optional session scopes."""
        request_id = str(uuid.uuid4())
        try:
            with self.container.scope("request", request_id):
                if "session" in scope:
                    session_id = _get_or_create_session_id(scope)
                    with self.container.scope("session", session_id):
                        await self.app(scope, receive, send)
                else:
                    await self.app(scope, receive, send)
        finally:
            _cleanup_scope(self.container, "request", request_id)

    async def _handle_websocket(self, scope, receive, send):
        """Handle WebSocket connection with websocket scope."""
        websocket_id = str(uuid.uuid4())
        try:
            with self.container.scope("websocket", websocket_id):
                await self.app(scope, receive, send)
        finally:
            _cleanup_scope(self.container, "websocket", websocket_id)
