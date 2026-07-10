# Docstring conventions

Public API docstrings in `src/lib/` and `src/add_ons/` are rendered on [ReadTheDocs](https://pydisplay.readthedocs.io) via mkdocstrings. Follow these rules so generated reference pages stay accurate.

## Style

- **Google style** only (`Args`, `Returns`, `Raises`, `Example`).
- Do not mix Sphinx directives (`:return:`, `:param:`).
- Match **real function signatures** — do not document named parameters on `*args` / `**kwargs` wrappers.

## Module docstrings

One-line summary of the module's role. Optionally link to narrative docs:

```python
"""
displaysys display drivers.

See also: https://pydisplay.readthedocs.io/en/latest/concepts/displays/
"""
```

## Class docstrings

- What the class is for and when to use it vs alternatives.
- `Args` for constructor parameters when non-obvious.
- Short usage example only when setup is not obvious (e.g. `Runtime`, `BusDisplay`).

## Method / function docstrings

| Section | When required |
|---------|----------------|
| Summary line | Always |
| `Args` | Public methods with parameters |
| `Returns` | When return value matters (especially `Area` bounds) |
| `Raises` | When callers must handle errors |
| `Example` | Non-obvious usage only |

## pydisplay-specific notes

- **`Area` returns:** Many `graphics` methods return an `Area` (`x`, `y`, `w`, `h`) for partial refresh.
- **Runtime:** Document poll/subscribe patterns; link to [Events concept](../concepts/events.md).
- **Delegates:** `Draw` and `FrameBuffer` shape methods delegate to `graphics._shapes` — signatures must match.
- **Private API:** Names starting with `_` are excluded from mkdocstrings output; minimal or no docstrings are fine.

## Verification

From the repo root:

```bash
.venv-docs/bin/mkdocs build 2>&1 | grep -i griffe
```

Griffe warnings mean a docstring parameter does not appear in the signature — fix before merging P0 module changes.

## Priority tiers

| Tier | Modules |
|------|---------|
| P0 | `displaysys`, `eventsys`, `graphics.FrameBuffer`, `graphics._shapes` |
| P1 | `graphics.Draw`, `displaybuf`, `eventsys` helpers |
| P2 | ✅ `pdwidgets` — done: Google-style docstrings on all public classes/methods (lifecycle `Display.tick`/`render`/event registration + every widget) |

See [Contributing](../contributing.md) for the PR workflow.
