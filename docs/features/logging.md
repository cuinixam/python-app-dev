# Logging != print()

Logging is not the same as printing to the console. Logging is a more sophisticated way of recording events in a program.
It is a way to track the flow of the program and to record errors and exceptions.

```{item} REQ-LOGGING_FILE-0.0.1 Print to file

   Print the log messages both to the console and to a file.
   The user **shall** be able to specify the log file path.
```

```{item} REQ-LOGGING-2.0.0 Easy Setup and Use

   Be easy to set up and use across all modules.
```

```{item} REQ-LOGGING-3.0.0 Handle Custom Exceptions

   Be capable of handling and logging custom exceptions.
```

```{item} REQ-LOGGING-4.0.0 Console Error Visibility

   Ensure error messages are clearly visible in the console, for instance, by printing them in red.
```

```{item} REQ-LOGGING-5.0.0 Special Error Log File

   Maintain a special log file specifically for error messages.
```

```{item} REQ-LOGGING-6.0.0 Log File Rotation

   Rotate log files, preserving the last two or three files before discarding older ones.
```

```{item} REQ-LOGGING_TIME_IT-0.0.1 Timing Methods

   Support special methods for timing and logging the execution of code blocks.

```

:::{note}
This module is based on the [loguru](https://github.com/Delgan/loguru) library, which is a Python logging library that provides powerful logging system.
:::

## Current Status

```{eval-rst}
.. item-matrix:: Traceability matrix
    :source: REQ-LOGGING
    :target: IMPL [IU]TEST
    :sourcetitle: Requirement
    :targettitle: Implementation, Test Cases
    :stats:
```
