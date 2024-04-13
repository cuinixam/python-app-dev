from enum import Enum
from typing import Any, Callable, Dict, List

EventCallback = Callable[..., None]
EventTrigger = Callable[..., None]


class EventID(Enum):
    pass


class EventManager:
    """
    Manages events and their subscribers.

    One can register callbacks to specific events with any number of arguments.
    When an event is triggered, all subscribers are called
    TODO: There is no check if the callback has the correct number of arguments.
    """

    def __init__(self) -> None:
        self._events: Dict[EventID, List[EventCallback]] = {}

    def create_event_trigger(self, event_id: EventID) -> EventTrigger:
        """Creates a lambda function that can be used to trigger a specific event."""
        return lambda *args, **kwargs: self._trigger_event(event_id, *args, **kwargs)

    def _trigger_event(self, event_id: EventID, *args: Any, **kwargs: Any) -> None:
        """Triggers an event and calls all subscribers."""
        for callback in self._events.get(event_id, []):
            callback(*args, **kwargs)

    def subscribe(self, event_id: EventID, callback: EventCallback) -> None:
        """Subscribes a callback to an event."""
        if self.is_already_subscribed(event_id, callback):
            raise ValueError(f"Callback {callback} is already subscribed to event {event_id}")
        self._events.setdefault(event_id, []).append(callback)

    def unsubscribe(self, event_id: EventID, callback: EventCallback) -> None:
        """Unsubscribes a callback from an event."""
        self._events[event_id].remove(callback)

    def is_already_subscribed(self, event_id: EventID, callback: EventCallback) -> bool:
        """Checks if a callback is already subscribed to an event."""
        return callback in self._events.get(event_id, [])
