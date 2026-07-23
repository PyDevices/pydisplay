# Handoff: Raised / gradient faces for pdwidgets — CLOSED

**Status:** complete (2026-07-23)

## Outcome

- **pdwidgets:** merged as [PR #13](https://github.com/PyDevices/pdwidgets/pull/13)
  (`style="raised"` on Button / IconButton / Chip / Card / SegmentedControl;
  shared `_raised` helper; default remains flat).
- **pydisplay demos:** `widgets_demo`, `widgets_actions`, `widgets_form_kitchen`
  exercise raised faces.
- **Consumer:** `roku_widgets` uses `style="raised"` with role-specific
  `bg_hi` / `bg_lo` / `rim` matching `roku_graphics._role_colors`.

## Acceptance criteria

- [x] Default `Button(...)` looks and presses exactly as before (flat).
- [x] `Button(..., style="raised")` shows top-lit gradient + rim; press inverts lighting.
- [x] `IconButton(..., style="raised")` works.
- [x] Chip and Card raised without breaking defaults.
- [x] No required new args; no breaking ColorTheme changes.
- [x] Listed examples (and pdwidgets_bench) demonstrate raised vs flat.
- [x] PR opened with summary + test plan → merged.
- [x] Smoke: widgets examples + `roku_widgets` via example_test_kit (cpython-venv).

## Historical brief

Original goal: opt-in raised faces in **pdwidgets** matching
`roku_graphics._draw_button`, without breaking flat `Button`. Roku wiring was
explicitly out of scope for the cloud agent task and landed afterward in
`roku_widgets` once the library shipped.

No further work required on this handoff.
