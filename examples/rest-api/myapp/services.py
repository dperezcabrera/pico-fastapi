from pico_ioc import component

from .config import GreetingConfig

GREETINGS = {
    "en": "Hello",
    "es": "Hola",
    "fr": "Bonjour",
}


@component
class GreeterService:
    def __init__(self, config: GreetingConfig):
        self.language = config.default_language

    def greet(self, name: str) -> str:
        greeting = GREETINGS.get(self.language, "Hello")
        return f"{greeting}, {name}!"

    def farewell(self, name: str) -> str:
        return f"Goodbye, {name}!"
