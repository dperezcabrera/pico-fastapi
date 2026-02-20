"""Configuration primitives for pico-fastapi.

Defines :class:`FastApiSettings` (application metadata loaded from config)
and the :class:`FastApiConfigurer` protocol (pluggable setup hooks with
priority-based ordering).
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from fastapi import FastAPI
from pico_ioc import configured


@runtime_checkable
class FastApiConfigurer(Protocol):
    """Protocol for pluggable FastAPI configuration hooks.

    Implement this protocol to add middleware, mount sub-apps, register
    error handlers, or perform any other app-level setup.  Configurers are
    discovered automatically by pico-ioc when decorated with ``@component``.

    The ``priority`` attribute controls ordering relative to
    ``PicoScopeMiddleware``:

    - **priority < 0** -- *outer* middleware, applied **before** the scope
      middleware (e.g. CORS, session).
    - **priority >= 0** -- *inner* middleware, applied **after** the scope
      middleware (e.g. auth, business-logic hooks).

    Within the same group, lower values execute first.

    Attributes:
        priority: Integer that determines execution order.  Defaults to ``0``.

    Example:
        .. code-block:: python

            from pico_ioc import component
            from pico_fastapi import FastApiConfigurer
            from fastapi import FastAPI

            @component
            class CORSConfigurer(FastApiConfigurer):
                priority = -100

                def configure_app(self, app: FastAPI) -> None:
                    from fastapi.middleware.cors import CORSMiddleware
                    app.add_middleware(
                        CORSMiddleware,
                        allow_origins=["*"],
                    )
    """

    @property
    def priority(self) -> int:
        return 0

    def configure_app(self, app: FastAPI) -> None:
        """Apply configuration to the FastAPI application.

        Args:
            app: The FastAPI application instance to configure.
        """
        ...


@configured(target="self", prefix="fastapi", mapping="tree")
@dataclass
class FastApiSettings:
    """Type-safe application settings for the FastAPI instance.

    Populated automatically from configuration sources (YAML, env, dict)
    using the ``fastapi`` prefix via pico-ioc's ``@configured`` decorator.
    The ``FastApiAppFactory`` converts these fields into keyword arguments
    for the ``FastAPI()`` constructor.

    Attributes:
        title: API title shown in the OpenAPI docs.
        version: API version string.
        debug: Enable FastAPI debug mode.

    Example:
        .. code-block:: yaml

            # application.yaml
            fastapi:
              title: My API
              version: 2.0.0
              debug: true
    """

    title: str = "Pico-FastAPI App"
    version: str = "1.0.0"
    debug: bool = False
