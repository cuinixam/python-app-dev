# Model-View-Presenter

```{eval-rst}
.. mermaid::

   flowchart
      P[Presenter] -->|subscribe| E[EventManager]
      E --> |notify| P
      V[View] -->|trigger| E
      P --> |update_data| V

```

In this diagram, you can see the three main components: View, Presenter, and Event Manager.
The Event Manager handles the events and subscriptions, while the Presenter mediates between the View and the underlying functionality.
The View interacts with the user and triggers events that are handled by the Event Manager.
The Presenter subscribes to the Event Manager to handle these events and updates the View accordingly.

```{eval-rst}
.. mermaid::

   classDiagram
      class View{
         +event_manager: EventManager
         +update_data()
      }

      class EventManager{
         -subscribers
         +create_event:trigger(event_id) callable
         +subscribe(event_id, callable)
         +unsubscribe(event_id, callable)
      }

      class Presenter{
         +event_manager: EventManager
         +view: View
         +run()
      }

      View "1" *-- EventManager
      Presenter "1" *-- View
      Presenter "1" *-- EventManager
```

Keeping the View and Presenter apart, with the Event Manager between them, makes the Presenter unit-testable without a user interface and lets the same logic drive a different View (for example, swapping a GUI for a command line).

## Event Manager

The `EventManager` decouples the View from the Presenter: the View raises events with `create_event_trigger`, and the Presenter reacts to them with `subscribe`. When an event fires, the manager calls every registered callback; `unsubscribe` removes one. This is the Observer pattern, with the manager as the subject and the callbacks as the observers, so neither side needs to know about the other.

```{eval-rst}
.. autoclass:: py_app_dev.mvp.event_manager::EventManager
   :members:
   :undoc-members:
```
