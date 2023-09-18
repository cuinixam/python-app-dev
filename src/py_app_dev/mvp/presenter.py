from typing import Protocol

from .event_manager import EventManager
from .view import View


class Presenter(Protocol):
    def __init__(self, view: View, event_manager: EventManager) -> None:
        ...

    def run(self) -> None:
        ...
