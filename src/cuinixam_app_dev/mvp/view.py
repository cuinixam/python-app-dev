from typing import Protocol

from .event_manager import EventManager


class View(Protocol):
    def __init__(self, event_manager: EventManager) -> None:
        ...
