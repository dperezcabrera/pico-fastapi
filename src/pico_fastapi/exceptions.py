class PicoFastAPIError(Exception):
    pass


class NoControllersFoundError(PicoFastAPIError):
    def __init__(self):
        super().__init__("No controllers were registered. Ensure your controller modules are scanned.")
