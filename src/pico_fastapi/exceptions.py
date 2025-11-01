class PicoFastAPIError(Exception):
    pass

class InvalidConfigurerError(PicoFastAPIError):
    def __init__(self, obj: object):
        super().__init__(f"Object does not implement FastApiConfigurer.configure(app): {obj!r}")

class NoControllersFoundError(PicoFastAPIError):
    def __init__(self):
        super().__init__("No controllers were registered. Ensure your controller modules are scanned.")

