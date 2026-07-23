# Handoff: Raised / gradient faces for pdwidgets (Button + parity widgets)

## Goal

Add an **opt-in** “raised” (top-lit vertical gradient + rim) face style to
**pdwidgets**, matching the look of pydisplay’s `roku_graphics` `_draw_button`,
without breaking the existing flat `Button` API.

Primary repo: **[PyDevices/pdwidgets](https://github.com/PyDevices/pdwidgets)**  
Reference implementation: `~/gh/pydevices/pydisplay/src/examples/roku_remote/roku_graphics.py`
(`_draw_button`, `_role_colors`, `_lerp`, `_shade`).

Demo examples live in the sibling **pydisplay** repo under `src/examples/widgets_*.py`.
Update **a few** of those (listed below), not the whole set.

On completion: open a **pull request** (pdwidgets required; pydisplay examples as a
second PR if the workspace has both repos writable).

Do **not** change `roku_widgets` / `roku_graphics` in this task unless needed only
to import/test against a local editable pdwidgets.

---

## Non-goals

- Do not make raised the default.
- Do not add a roku-local Button subclass in pydisplay examples beyond passing new kwargs.
- Do not rewrite LVGL or graphics front ends.
- Do not change ColorTheme defaults in a breaking way (additive helpers OK).
- Do not commit upstream `micropython/` / `circuitpython/` trees if present in a cmods workspace.

---

## Visual / behavior contract (match graphics)

Raised face when enabled:

1. Vertical top-lit gradient from `bg_hi` → `bg_lo` (or auto-derived from `bg`).
2. Soft darker rim stroke (`round_rect` outline).
3. Respect `radius` (including near-circular / pill when radius ≈ half min side).
4. **Pressed**: invert lighting (hi/lo swap), same as graphics — not merely an outline.
5. Label/icon sit on top; label background must be **transparent** in raised mode so
   the gradient isn’t covered by a solid text plate.
6. Optional existing `shadow` still works (draw shadow first, then raised face).

Flat mode (`style="flat"` / default): **same behavior as today**
(solid `round_rect` fill; press = outline with `fg`).

---

## Suggested API (API-safe)

On `pdwidgets.widgets.button.Button` (and thus `IconButton` via inheritance):

```python
style="flat",          # or "raised"; default "flat"
bg_hi=None,            # optional; default shade(bg, ~1.12)
bg_lo=None,            # optional; default shade(bg, ~0.78)
rim=None,              # optional; default shade(bg, ~0.55)
```

Rules:

- New kwargs optional with defaults → existing call sites unchanged.
- Prefer accepting only known `style` values; invalid → `ValueError` or fall back to flat (document choice).
- Auto-derive hi/lo/rim from `bg` when omitted (RGB565 channel math like graphics `_shade` / `_lerp`).
- Keep `bg` as the “face” mid color used for derivation and for flat fill.

Shared helper (required):

- `pdwidgets/widgets/_raised.py` or `pdwidgets/_draw_raised.py` with:
  - `shade(c, factor)`, `lerp(c1, c2, t)`
  - `fill_raised_round_rect(fb, x, y, w, h, radius, hi, lo, rim, pressed=False)`
- Reuse from Button, Chip, Card, etc.

---

## Widgets that need parity (scope)

### Must

1. **`Button`** — implement raised draw + pressed invert; transparent label bg when raised.
2. **`IconButton`** — inherits Button; verify icon still centers and press works.

### Should (same face language; opt-in `style=`)

3. **`Chip`** — selected/unselected fills currently flat `round_rect`; add `style="raised"` so selected chips can look like raised keys.
4. **`Card`** — support opt-in `style="raised"` via the shared helper (keep default flat + existing shadow).

### Nice (shared helper makes it cheap)

5. **`SegmentedControl`** — raised fill on the **selected** segment only when `style="raised"`.
6. Toast / dialog action buttons — only if they construct `Button` (they get it for free).

### Out of scope for this PR

- Slider / Switch thumbs (different metaphor)
- TextInput / Dropdown field chrome
- ProgressBar, Gauge, Chart
- Full theme redesign

---

## Implementation steps

1. Read reference: `roku_graphics._draw_button` (gradient loop + circular inset + rim + pressed invert).
2. Add shared RGB565 shade/lerp + raised fill helper under pdwidgets (no dependency on roku).
3. Extend `Button.__init__` / `draw` / `press` / `release`:
   - flat → existing path
   - raised → full redraw on press/release (invalidate/draw), inverted gradient when pressed
4. When creating the child `Label`, if raised: pass theme transparent as label `bg`.
5. Extend Chip and Card with the same `style` defaulting to flat.
6. Extend SegmentedControl selected segment if time allows (nice).
7. Update **selected** pydisplay examples (below).
8. Extend `tools/pdwidgets_bench.py` with flat + raised buttons side by side.
9. Lint/format per pdwidgets norms (ruff if configured).
10. Open PR(s).

Performance note: row-by-row `fill_rect` is fine for desktop / occasional MCU demos;
keep flat as default. Avoid large scratch buffers unless needed for circular inset
correctness; prefer drawing clipped to `padded_area` on `display.framebuf` if that
matches pdwidgets patterns.

---

## Examples to update (pydisplay) — not all

Update these **three** only:

| Example | Why |
|---------|-----|
| `src/examples/widgets_demo.py` | Smallest Button showcase; add `style="raised"` on the center anchor (and maybe one align label button). |
| `src/examples/widgets_actions.py` | Menu Button + Chips; set raised on the Menu button and on Chips if Chip supports style. |
| `src/examples/widgets_form_kitchen.py` | Form controls with many Buttons; raise primary/action buttons only (leave the rest flat to show contrast). |

Do **not** modify: `widgets_percent`, `widgets_device_panel`, `widgets_smartwatch`,
`widgets_settings`, `widgets_nav_tabs`, `widgets_media_busy`, `widgets_gauge_dash`,
`widgets_sheets`, `widgets_pickers` (unless a one-line import break forces a fix).

If the cloud workspace cannot write pydisplay, put a raised vs flat strip in
`pdwidgets/tools/pdwidgets_bench.py` instead and note that in the PR.

Editable install: ensure pydisplay examples see the local pdwidgets
(`PYTHONPATH=../pdwidgets/src` or existing sibling `.pth` / `setup_sibling_repos.sh`).

---

## Acceptance criteria

- [ ] Default `Button(...)` looks and presses exactly as before (flat).
- [ ] `Button(..., style="raised")` shows top-lit gradient + rim; press inverts lighting.
- [ ] `IconButton(..., style="raised")` works.
- [ ] Chip and Card raised (if implemented) without breaking defaults.
- [ ] No required new args; no breaking ColorTheme changes.
- [ ] At least the listed examples (or bench) demonstrate raised vs flat.
- [ ] PR opened with summary + test plan.
- [ ] Smoke: import + construct raised Button on CPython with dummy SDL if available:

```bash
# from pydisplay, with sibling pdwidgets on path
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  .venv/bin/python tools/example_test_kit.py --no-unit-tests \
  --only-runtime cpython-venv --only-example widgets_demo
```

  (or equivalent bench run in pdwidgets)

---

## PR instructions

### pdwidgets (required)

1. Branch from latest `main`, e.g. `raised-button-faces`.
2. Commit with a focused message, e.g.  
   `Add opt-in raised gradient faces for Button and Chip`
3. Push and create PR with `gh pr create`:

```bash
gh pr create --title "Add opt-in raised (gradient) button faces" --body "$(cat <<'EOF'
## Summary
- Opt-in `style="raised"` for Button/IconButton (default remains flat)
- Shared shade/lerp raised fill helper; pressed inverts lighting (roku_graphics parity)
- Chip and Card support the same opt-in style

## Test plan
- [ ] Existing flat Button call sites unchanged
- [ ] Raised Button / IconButton visual + press invert on desktop
- [ ] widgets_demo / widgets_actions / widgets_form_kitchen (or pdwidgets_bench) smoke
- [ ] ruff / existing pdwidgets tests if present

EOF
)"
```

### pydisplay examples (if writable)

Second PR on pydisplay updating only the three examples above, depending on the
pdwidgets change (note the pdwidgets PR URL in the body). If examples are updated
in the same cloud workspace without publishing pdwidgets, document that reviewers
need the sibling checkout.

---

## Reference snippets (do not copy blindly — adapt to pdwidgets)

Graphics pressed/role colors and gradient loop live in:

- `pydisplay/src/examples/roku_remote/roku_graphics.py` ≈ `_role_colors`, `_draw_button`

pdwidgets current Button draw/press:

- `pdwidgets/src/pdwidgets/widgets/button.py` (`draw`, `press`, `release`)

---

## Engineering constraints (Brad)

- Fix root cause in pdwidgets; no roku-local workaround subclass.
- Small, reviewable diffs; revert dead experiments.
- Do not ask the user to reproduce — run smokes yourself and report evidence.
- After success: PR URL in the final message.
