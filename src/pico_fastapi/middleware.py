"""ASGI middleware for pico-ioc scope lifecycle management.

:class:`PicoScopeMiddleware` creates and cleans up ``request``, ``session``,
and ``websocket`` scopes so that pico-ioc components scoped to these
lifecycles are resolved and disposed of automatically.
"""

import uuid

from pico_ioc import PicoContainer


def _cleanup_scope(container: PicoContainer, scope_name: str, scope_id: str) -> None:
    """Clean up a scope if the container has caches.

    Args:
        container: The pico-ioc container instance.
        scope_name: Name of the scope to clean up (e.g. ``"request"``).
        scope_id: Unique identifier of the scope instance.
    """
    if hasattr(container, "_caches"):
        container._caches.cleanup_scope(scope_name, scope_id)


def _get_or_create_session_id(scope: dict) -> str:
    """Get the existing session ID or create a new one.

    Session IDs are stored in the ASGI scope's ``session`` dict under
    the ``pico_session_id`` key.

    Args:
        scope: The ASGI scope dict.  Must contain a ``"session"`` key
            (provided by Starlette's ``SessionMiddleware``).

    Returns:
        The session identifier string (UUID4).
    """
    session = scope["session"]
    if "pico_session_id" not in session:
        session["pico_session_id"] = str(uuid.uuid4())
    return session["pico_session_id"]


class PicoScopeMiddleware:
    """ASGI middleware that manages pico-ioc request, session, and websocket scopes.

    For every HTTP request, a ``request`` scope is created (and optionally a
    ``session`` scope if ``SessionMiddleware`` is active).  For every
    WebSocket connection, a ``websocket`` scope is created.  Scopes are
    cleaned up in a ``finally`` block to prevent memory leaks.

    This middleware is added automatically by ``PicoLifespanConfigurer``
    and should not be added manually.

    Args:
        app: The next ASGI application in the middleware chain.
        container: The pico-ioc container whose scopes are managed.

    Example:
        .. code-block:: python

            # Automatic -- no manual setup required.
            # PicoLifespanConfigurer adds PicoScopeMiddleware for you.
            container = init(modules=["myapp"])
            app = container.get(FastAPI)
    """

    def __init__(self, app, container: PicoContainer):
        self.app = app
        self.container = container

    async def __call__(self, scope, receive, send):
        """Dispatch incoming ASGI connections to the appropriate handler.

        Args:
            scope: ASGI connection scope dict.
            receive: ASGI receive callable.
            send: ASGI send callable.
        """
        with self.container.as_current():
            scope_type = scope["type"]

            if scope_type == "http":
                await self._handle_http(scope, receive, send)
            elif scope_type == "websocket":
                await self._handle_websocket(scope, receive, send)
            else:
                await self.app(scope, receive, send)

    async def _handle_http(self, scope, receive, send):
        """Handle HTTP request with request and optional session scopes.

        Creates a unique ``request`` scope for every HTTP request.  If
        a ``"session"`` key is present in the ASGI scope (provided by
        ``SessionMiddleware``), a ``session`` scope is also created.

        Args:
            scope: ASGI HTTP connection scope.
            receive: ASGI receive callable.
            send: ASGI send callable.
        """
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
        """Handle WebSocket connection with websocket scope.

        Creates a ``websocket`` scope that lasts for the entire WebSocket
        connection lifetime.  The scope is cleaned up when the connection
        closes.

        Args:
            scope: ASGI WebSocket connection scope.
            receive: ASGI receive callable.
            send: ASGI send callable.
        """
        websocket_id = str(uuid.uuid4())
        try:
            with self.container.scope("websocket", websocket_id):
                await self.app(scope, receive, send)
        finally:
            _cleanup_scope(self.container, "websocket", websocket_id)
