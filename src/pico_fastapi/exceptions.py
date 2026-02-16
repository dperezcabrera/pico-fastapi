"""Custom exceptions for pico-fastapi.

All pico-fastapi exceptions inherit from :class:`PicoFastAPIError`,
allowing callers to catch the base class at application boundaries.
"""


class PicoFastAPIError(Exception):
    """Base exception for all pico-fastapi errors.

    Catch this at startup boundaries to handle any pico-fastapi failure
    without matching individual subclasses.

    Example:
        .. code-block:: python

            try:
                app = container.get(FastAPI)
            except PicoFastAPIError as exc:
                logger.error("pico-fastapi startup failed: %s", exc)
                raise
    """


class NoControllersFoundError(PicoFastAPIError):
    """Raised when no ``@controller``-decorated classes are found at startup.

    This error is raised by ``register_controllers()`` when the pico-ioc
    container does not contain any classes marked with the ``@controller``
    decorator.

    Causes:
        - Controller modules were not included in ``init(modules=[...])``.
        - Controller classes are missing the ``@controller`` decorator.
        - Import errors prevented controller modules from loading.

    Example:
        .. code-block:: python

            try:
                register_controllers(app, container)
            except NoControllersFoundError:
                logger.warning("No controllers found; API has no endpoints.")
    """

    def __init__(self):
        super().__init__("No controllers were registered. Ensure your controller modules are scanned.")
