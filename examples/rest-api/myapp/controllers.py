from pico_fastapi import controller, get

from .services import GreeterService


@controller(prefix="/api/greet", tags=["Greetings"])
class GreetingController:
    """Controller for greeting endpoints."""

    def __init__(self, service: GreeterService):
        self.service = service

    @get("/{name}")
    async def say_hello(self, name: str):
        """Greet a user by name."""
        message = self.service.greet(name)
        return {"message": message}

    @get("/{name}/goodbye")
    async def say_goodbye(self, name: str):
        """Say goodbye to a user."""
        message = self.service.farewell(name)
        return {"message": message}
