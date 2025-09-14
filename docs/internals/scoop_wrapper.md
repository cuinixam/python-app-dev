# Scoop Wrapper

- search for the scoop executable and throws an error if not found
- searches for all `manifest.json` files to determine all scoop installed apps
- determine all apps to be installed but missing (need to be installed)
- create a temporary `scoopfile.json` with only the missing apps
- run `scoop import scoopfile.json`
- collect all installed tools

## Implementation

```{automodule} py_app_dev.core.scoop_wrapper
   :members:
   :show-inheritance:
```

## Testing

```{automodule} test_scoop_wrapper
   :members:
   :show-inheritance:

```
