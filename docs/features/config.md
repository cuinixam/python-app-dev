# Configuration

The `py_app_dev.core.config` module is the single home for the configuration-dataclass idiom: define a schema once as a [mashumaro](https://github.com/Fatal1ty/mashumaro) dataclass, then parse, merge, locate and export it the same way in every application.

## Schema mixins

Two base mixins carry the project-wide serialization policy (`omit_none`, `serialize_by_alias`):

- `BaseConfigDictMixin` — dict in/out (`from_dict`/`to_dict`).
- `BaseConfigJSONMixin` — adds JSON file I/O (`from_file`, `to_json_file`, `to_json_string`).

```python
@dataclass
class ToolEntry(BaseConfigJSONMixin):
    name: str
    version: str
    url_base: str | None = field(default=None, metadata={"alias": "url-base"})
```

Aliased fields round-trip by their wire name (`url-base`), `None` fields are omitted from output.

## Parsing files

Two explicit functions, same formats (`.json`, `.yaml`, `.yml`) and same error handling (a `UserNotificationException` naming the file on any syntax error or unsupported format):

- `parse_dict_from_file(path)` — plain parse into a dict.
- `parse_located_dict_from_file(path)` — additionally stamps every YAML mapping with its `file:line:column` as a dict *attribute* (never a key — the content is identical to the plain parse). Use it when the result feeds a `ConfigElement`; the provenance entry points below use it internally.

## Configs with a source file: `ConfigFile`

When the application must remember *which file* a config came from (cache invalidation, diagnostics, merging multiple sources), wrap the payload in the generic carrier instead of polluting the schema with a path field:

```python
class ToolsConfigFile(ConfigFile[ToolsConfig]):  # one line binds the payload type
    pass

source = ToolsConfigFile.from_file(Path("tools.yaml"))
source.payload   # the parsed ToolsConfig
source.file      # Path("tools.yaml"); None for in-memory instances
```

Override `from_dict` when the wire format nests the payload under a key.

## Merging multiple sources

Two merge policies, matching two config shapes:

- `merge_configs(base, override)` — dict-shaped configs; override's values win, nested dicts merge recursively.
- `merge_named_elements(target, source)` — lists of named elements (tools, dependencies, …); union by `name`, where a later element with an existing name **overrides** it, like git config files (system → global → local).

Only `merge_named_elements` preserves source locations: it keeps the winning element object, which carries its own `location`. `merge_configs` rebuilds the result through `to_dict()`/`from_dict()`, so the merged object is unlocated.

```python
merged = ToolsConfig()
for source in [base, level1, level2]:          # order defines override priority
    merge_named_elements(merged.tools, source.payload.tools)
```

See `tests/test_config.py::test_three_config_files_merge_with_override_and_store_result` for the complete flow: three files → override merge → stored result.

## Source-location provenance: `ConfigElement`

A config dataclass that inherits `ConfigElement` knows where each of its elements was declared — file, 1-based line and column:

```python
@dataclass
class ServerConfig(ConfigElement):
    host: str
    port: int = 8080

config = parse_config_element(ServerConfig, Path("server.yaml"))
config.location           # server.yaml:1:1
```

What you get, with nothing to wire up:

- **Every nested element is located.** The YAML loader records each mapping's position as an *attribute* on the parsed dict (never a key — payloads forwarded verbatim to other tools stay byte-clean), and the deserializer lifts it into the element.
- **Pinpointed errors.** A schema violation reports the exact element: `Failed to parse configuration at server.yaml:3:5: Field "port" …` — via `parse_config_element` and equally via a `ConfigFile[...].from_file` carrier.
- **Provenance never leaks.** `location` is metadata, not value: excluded from equality and repr, stripped from `to_dict()`. The backing field is named `_source_location` with no alias, so the field name *is* the wire key and no serialization policy can separate them; subclasses declaring `_source_location` or `location` are rejected at class-definition time.

Limits: JSON files parse without positions (`location` is `None`); positions are per-mapping, not per-scalar.

## Putting it together

A multi-source application config typically combines all three layers: `ConfigElement` payloads (located elements), `ConfigFile` carriers (which file), and `merge_named_elements` (override order). `tests/test_config_provenance.py` doubles as the usage reference — each test documents one behavior.
