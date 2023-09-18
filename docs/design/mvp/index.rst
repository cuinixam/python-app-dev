Model-View-Presenter
####################

.. mermaid::

   flowchart
      P[Presenter] -->|subscribe| E[EventManager]
      E --> |notify| P
      V[View] -->|trigger| E
      P --> |update_data| V


In this diagram, you can see the three main components: View, Presenter, and Event Manager.
The Event Manager handles the events and subscriptions, while the Presenter mediates between the View and the underlying functionality.
The View interacts with the user and triggers events that are handled by the Event Manager.
The Presenter subscribes to the Event Manager to handle these events and updates the View accordingly.

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

The implementation above uses the Model-View-Presenter (MVP) design pattern along with the Event Manager to handle events and communication between the components.
Here are some advantages of this implementation:

* **Separation of Concerns:**
   This pattern pattern separates the responsibilities of the View and Presenter into distinct components, which makes the code easier to read, test, and maintain.
   The Event Manager also helps to decouple the components, making it easier to modify and extend the code without affecting other parts.
* **Testability:**
   The Presenter acts as a mediator between the View and the underlying functionality, which allows for easy unit testing of the Presenter without needing to test the user interface.
* **Flexibility:**
   It allows for different user interfaces to be used with the same underlying functionality.
   For example, if we wanted to switch from a graphical user interface to a command-line interface, we could do so without affecting the underlying functionality of the application.


Event Manager
=============

The EventManager class is a utility class that can be used in conjunction with the Model-View-Presenter design pattern to facilitate communication between the View and the Presenter.
Its primary purpose is to handle events that are raised by the View and forward them to the appropriate Presenter methods.


By using the EventManager class, the View can raise events using the create_event_trigger method, and the Presenter can subscribe to those events using the subscribe method.
When the event is triggered, the EventManager calls all of the registered callbacks for that event, allowing the Presenter to handle the event appropriately.
The unsubscribe method can be used to remove callbacks from the list of subscribers if needed.

It's worth noting that the EventManager class, as described above, is actually an implementation of the Observer design pattern.
In this pattern, the EventManager acts as the Subject or Observable, while the callbacks registered through the subscribe method serve as the Observers.

When an event is triggered, the EventManager notifies all registered Observers by calling their respective callback functions. This decouples the components of the system and allows for easier maintenance and modifications in the future.

By using the Observer pattern with the EventManager class, the View can raise events without knowing anything about the Presenter, and the Presenter can handle events without knowing anything about the View. This promotes a more modular and flexible architecture, making it easier to develop and maintain complex systems.

.. autoclass:: py_app_dev.mvp.event_manager::EventManager
   :members:
   :undoc-members:
