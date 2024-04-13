# Logging

## Requirements

```{eval-rst}
.. item:: REQ-LOGGING_FILE-0.0.1 Print to file
   :status: Approved

   It **shall** be possible to print the log messages both to the console and to a file.
   The user **shall** be able to specify the log file path.
```

```{eval-rst}
.. item:: REQ-LOGGING-2.0.0 Easy Setup and Use
   :status: Approved

   It **shall** be easy to set up and use across all modules.
```

```{eval-rst}
.. item:: REQ-LOGGING-3.0.0 Handle Custom Exceptions
   :status: Approved

   It **shall** be capable of handling and logging custom exceptions.
```

```{eval-rst}
.. item:: REQ-LOGGING-4.0.0 Console Error Visibility
   :status: Approved

   It **shall** ensure error messages are clearly visible in the console, for instance, by printing them in red.
```

```{eval-rst}
.. item:: REQ-LOGGING-5.0.0 Special Error Log File
   :status: Approved

   It **shall** maintain a special log file specifically for error messages.
```

```{eval-rst}
.. item:: REQ-LOGGING-6.0.0 Log File Rotation
   :status: Approved

   It **shall** rotate log files, preserving the last two or three files before discarding older ones.
```

```{eval-rst}
.. item:: REQ-LOGGING_TIME_IT-0.0.1 Timing Methods
   :status: Approved

   It **shall** support special methods for timing and logging the execution of code blocks.

```

## Implementation

```{eval-rst}
.. automodule:: py_app_dev.core.logging
   :members:
   :show-inheritance:
```

## Testing

```{eval-rst}
.. automodule:: test_logger
   :members:
   :show-inheritance:

```

## Reports

```{eval-rst}
.. item-matrix:: Trace requirements to implementation
    :source: REQ-LOGGING
    :target: IMPL
    :sourcetitle: Requirement
    :targettitle: Implementation
    :stats:
```

```{eval-rst}
.. item-matrix:: Requirements to test case description traceability
    :source: REQ-LOGGING
    :target: [IU]TEST
    :sourcetitle: Requirements
    :targettitle: Test cases
    :sourcecolumns: status
    :group: bottom
    :stats:
```
