# create tests for EventManager
from enum import auto
from typing import Any, List

import pytest

from py_app_dev.mvp.event_manager import EventID, EventManager


class MyEventID(EventID):
    EVENT1 = auto()


def test_event_manager_create_event_trigger():
    event_manager = EventManager()
    command = event_manager.create_event_trigger(MyEventID.EVENT1)
    assert command is not None


def test_subscribe():
    subscriber_notified = False

    def my_callback():
        nonlocal subscriber_notified
        subscriber_notified = True

    event_manager = EventManager()
    event_manager.subscribe(MyEventID.EVENT1, my_callback)
    trigger = event_manager.create_event_trigger(MyEventID.EVENT1)
    assert not subscriber_notified
    trigger()
    assert subscriber_notified


def test_unsubscribe():
    subscriber_notified = False

    def my_callback():
        nonlocal subscriber_notified
        subscriber_notified = True

    event_manager = EventManager()
    event_manager.subscribe(MyEventID.EVENT1, my_callback)
    trigger = event_manager.create_event_trigger(MyEventID.EVENT1)
    trigger()
    assert subscriber_notified
    subscriber_notified = False
    event_manager.unsubscribe(MyEventID.EVENT1, my_callback)
    trigger()
    assert not subscriber_notified


def test_is_already_subscribed():
    def my_callback():
        pass

    event_manager = EventManager()
    event_manager.subscribe(MyEventID.EVENT1, my_callback)
    assert event_manager.is_already_subscribed(MyEventID.EVENT1, my_callback)
    assert not event_manager.is_already_subscribed(MyEventID.EVENT1, lambda: None)


def test_can_not_subscribe_twice():
    def my_callback():
        pass

    event_manager = EventManager()
    event_manager.subscribe(MyEventID.EVENT1, my_callback)
    with pytest.raises(ValueError):
        event_manager.subscribe(MyEventID.EVENT1, my_callback)


def test_subscribe_with_args():
    received_args: List[Any] = []
    received_kwargs = {}

    def my_callback_with_args(*args, **kwargs):
        nonlocal received_args, received_kwargs
        received_args.extend(args)
        received_kwargs.update(kwargs)

    event_manager = EventManager()
    event_manager.subscribe(MyEventID.EVENT1, my_callback_with_args)
    trigger = event_manager.create_event_trigger(MyEventID.EVENT1)

    # Test with positional arguments
    trigger(42, "hello")
    assert received_args == [42, "hello"]

    # Reset for next test
    received_args.clear()

    # Test with keyword arguments
    trigger(foo=1, bar=2)
    assert received_kwargs == {"foo": 1, "bar": 2}
