from enum import Enum
from typing import Callable, Dict, List

EventCallback = Callable[[], None]
EventTrigger = Callable[[], None]


class EventID(Enum):
    pass


class EventManager:
    """Manages events and their subscribers."""

    def __init__(self) -> None:
        self._events: Dict[EventID, List[EventCallback]] = {}

    def create_event_trigger(self, event_id: EventID) -> EventTrigger:
        """Creates a lambda function that can be used to trigger a specific event."""
        return lambda: self._trigger_event(event_id)

    def _trigger_event(self, event_id: EventID) -> None:
        """Triggers an event and calls all subscribers."""
        for callback in self._events.get(event_id, []):
            callback()

    def subscribe(self, event_id: EventID, callback: EventCallback) -> None:
        """Subscribes a callback to an event."""
        if self.is_already_subscribed(event_id, callback):
            raise ValueError(
                f"Callback {callback} is already subscribed to event {event_id}"
            )
        self._events.setdefault(event_id, []).append(callback)

    def unsubscribe(self, event_id: EventID, callback: EventCallback) -> None:
        """Unsubscribes a callback from an event."""
        self._events[event_id].remove(callback)

    def is_already_subscribed(self, event_id: EventID, callback: EventCallback) -> bool:
        """Checks if a callback is already subscribed to an event."""
        return callback in self._events.get(event_id, [])
