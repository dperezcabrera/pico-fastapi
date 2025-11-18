import uuid
from pico_ioc import PicoContainer

class PicoScopeMiddleware:
    def __init__(self, app, container: PicoContainer):
        self.app = app
        self.container = container

    async def __call__(self, scope, receive, send):
        with self.container.as_current():
            if scope["type"] == "http":
                request_id = str(uuid.uuid4())
                try:
                    with self.container.scope("request", request_id):
                        if "session" in scope:
                            session = scope["session"]
                            if "pico_session_id" not in session:
                                session["pico_session_id"] = str(uuid.uuid4())
                            session_id = session["pico_session_id"]
                            with self.container.scope("session", session_id):
                                await self.app(scope, receive, send)
                        else:
                            await self.app(scope, receive, send)
                finally:
                    if hasattr(self.container, "_caches"):
                         self.container._caches.cleanup_scope("request", request_id)

            elif scope["type"] == "websocket":
                websocket_id = str(uuid.uuid4())
                try:
                    with self.container.scope("websocket", websocket_id):
                        await self.app(scope, receive, send)
                finally:
                    if hasattr(self.container, "_caches"):
                         self.container._caches.cleanup_scope("websocket", websocket_id)
            else:
                await self.app(scope, receive, send)
