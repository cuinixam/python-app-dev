# Install Scoop Apps

The [Scoop](https://scoop.sh/) package manager for Windows has certain limitations, particularly in handling of tool versions and path prioritization via shims.
This module allows users to specify which versions of apps they want installed and actively manage the accessibility of these apps within their environment.

## Usage

Point `ScoopWrapper` at a scoop file (the JSON listing the apps and versions you want). `install` installs anything missing and returns every required app, located on disk:

```python
from pathlib import Path

from py_app_dev.core.scoop_wrapper import ScoopWrapper

apps = ScoopWrapper().install(Path("scoopfile.json"))
for app in apps:
    print(app.name, app.version)
    print(app.get_all_required_paths())  # bin and env directories to put on PATH
```

Each returned `InstalledScoopApp` carries its `name`, `version`, install `path`, and the bin/env directories from its manifest.

## Requirements

```{item} REQ-SCOOP-WRAPPER-0.0.1 Customized App Installation

   Allow users to specify which apps and versions to install via Scoop.
```

```{item} REQ-SCOOP-WRAPPER-0.0.2 Locate Specific App Versions

   Locate specific versions of installed apps.

   ::: {note}
   Avoid the use of shims and do not consider the `current` symlinks to the latest versions.
   :::

```

```{item} REQ-SCOOP-WRAPPER-0.0.3 Collect Relevant Apps Directories

   Collect all apps relevant directories (e.g. `bin`, `lib`, `etc`) which are provided in the `manifest.json` file of every Scoop app.
```

::: {attention}
The provided environment must have Scoop installed.
:::
