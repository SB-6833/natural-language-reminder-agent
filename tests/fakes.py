from typing import Any


class FakeProvider:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls = 0

    def interpret(self, request: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        return self.response
