#!/usr/bin/env python3
"""Cross-backend input / keypad diagnostic (no LVGL required).

Use this when debugging keyboard, hardware keypad, or LVGL keypad mapping.
It exercises the same ``events.Key`` contract every displaydev backend must
emit, plus optional LVGL mapping when ``display_driver`` is importable.

## Layers (fix at the lowest layer that owns the bug)

1. **displaydev** (``sdldisplay`` / ``pgdisplay`` / ``psdisplay`` / ``jndisplay``)
   — native → ``events.Key`` conversion (repeat, scancode, mod, name).
2. **eventsys** (``HostEventsDevice``, ``KeypadDevice``, ``VirtualDevices``)
   — quit chords, hardware keypad, FIFO fan-out to virtual keypad.
3. **display_driver** (LVGL only) — ``_lv_key_from_event`` / keypad indev.

Plain (non-LVGL) apps consume layer 1→2 only via ``runtime.poll()`` /
``runtime.on(KEYDOWN, …)``. Do not "fix" typing in ``display_driver`` if
raw eventsys already looks wrong.

## Usage (from ``pydevices-examples`` repo root)

Self-tests (no window focus needed)::

    python tools/input_probe.py --selftest
    micropython tools/input_probe.py --selftest

Interactive host dump (needs ``lib/`` on path / ``board_config``; focus window)::

    cd lib && python ../tools/input_probe.py
    cd lib && micropython ../tools/input_probe.py

Print the historical fix checklist::

    python tools/input_probe.py --fixes

With LVGL mapping column (imports ``display_driver``)::

    cd lib && micropython ../tools/input_probe.py --lvgl

Quit: platform quit chord (usually Ctrl+Q).

## Historical fix checklist (A-H; implemented - see ``--fixes``)

Ordered by layer. Each item is a targeted change with acceptance criteria.

### A. eventsys — ``KeypadDevice`` name must not use ``chr(key)`` (multi-backend / HW)

- **Where:** ``eventsys/_keypad.py`` ``_poll``.
- **Bug:** ``chr(keys.K_UP)`` etc. raises ``ValueError`` (SDL scancode-masked
  codes). FunHouse ``board_config`` feeds ``keys.K_UP`` / ``K_DOWN``.
- **Fix:** Set ``name`` via ``keys.keyname(key)`` (or ``""`` / hex fallback),
  never ``chr(key)`` for arbitrary ints. Keep ``key`` as the int code.
- **Accept:** ``KeypadDevice(read=lambda: {keys.K_UP}).poll()`` returns a
  ``KEYDOWN``; FunHouse up/down no longer crash the auto-service tick.
- **Tests:** ``--selftest`` case ``keypad_chr_safe``; board smoke if available.

### B. displaydev — document + unify key-repeat policy (SDL/pygame vs browser)

- **Where:** ``sdldisplay._convert``, ``pgdisplay._convert`` vs
  ``psdisplay``/``jndisplay`` (already drop ``e.repeat``).
- **Bug:** Desktop floods ``KEYDOWN`` on hold; browser emits one. Apps that
  count downs (or LVGL keypad FIFO drain) behave differently per backend.
- **Fix (choose one contract, apply consistently):**
  1. **Preferred for parity with browser:** drop OS auto-repeat at SDL/pygame
     convert (``if e.key.repeat: continue`` / pygame equivalent), **or**
  2. Expose ``repeat`` on ``events.Key`` (new field or reuse unused slot) and
     document that consumers must ignore repeats if they want edge semantics;
     then stop silently dropping only on browser.
- **Accept:** Hold ``a`` for 2s → same ``KEYDOWN`` count on SDL and PyScript
  under the chosen contract; ``--selftest`` cannot fully prove OS repeat
  (manual hold in interactive mode + ``downs[key]`` counter).
- **Do not** coalesce only in LVGL — non-LVGL apps share this path.

### C. eventsys — keypad virtual-device FIFO backpressure (LVGL path, multi-display)

- **Where:** ``eventsys/_host.py`` ``VirtualDevice.add_event`` (keypad fifo).
- **Bug:** Only ``MOUSEMOTION`` coalesces; key fifo is uncapped; LVGL drains
  ~1 event per indev period. SDL repeat (B) + slow UI → lagged "playback".
- **Fix:** After (B) is decided:
  - If repeats dropped at backend: optional same-key KEYDOWN coalesce + purge
    pending downs for a key on KEYUP (narrow, documented).
  - If repeats kept: coalesce consecutive identical ``KEYDOWN`` (same key) in
    the keypad fifo, and/or cap fifo with drop-oldest and a counter/log.
- **Accept:** Hold Backspace 3s then type — no multi-second backlog of
  deletes; fifo length stays bounded under load (probe ``fifo_depth``).

### D. display_driver — do not feed non-text SDLKs into LVGL keypad (LVGL-only)

- **Where:** ``display_driver._lv_key_from_event`` / ``_keypad_cb``.
- **Bug:** Modifiers (``K_LSHIFT``…), F-keys, and other scancode-masked codes
  pass through as ``data.key``. Text widgets treat them as character codes →
  buffer corruption / ``UnicodeError`` on ``get_text()``.
- **Fix:** Map known navigation/edit keys to ``lv.KEY_*``; pass printable
  ASCII (and any intentional Unicode policy); **return a sentinel / skip
  updating ``data.key``** for modifiers and other non-text keys. Keep sticky
  press/release state so idle ``read_cb`` does not clear a real key.
- **Accept:** Shift alone never changes textarea contents; Shift+letter still
  produces a capital **if** the backend already delivers shifted text *or*
  after fix E; F1/modifiers never grow ``ta.get_text()`` with junk.

### E. display_driver — Shift / Caps for text entry (LVGL-only; after D)

- **Where:** ``_lv_key_from_event`` (and optional tracked mod mask in keypad cb).
- **Bug:** ``Shift+a`` currently maps to ``97`` (``'a'``) — LVGL does not apply
  ``event.mod``. Digits with Shift stay ``'1'`` not ``'!'``.
- **Fix:** Apply US (or layout-documented) shift map + Caps using ``event.mod``
  (group-aware ``KMOD_SHIFT`` / ``KMOD_CAPS``). Optionally OR in tracked
  modifier KEYDOWN/KEYUP bits if a host delivers stale ``mod`` on letter events.
- **Accept:** Interactive: ``AbC!`` via Shift; Caps Lock toggles letters;
  Ctrl/Alt alone still do not insert characters (D).

### F. display_driver — arrows: focus vs caret (LVGL-only, product choice)

- **Where:** ``_lv_key_from_event`` (today: arrows → ``NEXT``/``PREV`` focus).
- **Bug / mismatch:** Textareas cannot move the caret with arrows; arrows only
  change group focus. Tab already does focus next/prev.
- **Fix:** Map arrows to ``lv.KEY.LEFT/RIGHT/UP/DOWN`` for caret; keep Tab
  (and optionally encoder) for focus. Document for apps that relied on arrow
  focus (e.g. car_cluster already remaps via ``input_map``).
- **Accept:** In a focused textarea, arrows move caret; Tab still changes
  focus; car_cluster still works with its override.

### G. eventsys — browser ``mod_mask`` left-only (browser backends)

- **Where:** ``eventsys/keys.py`` ``mod_mask``.
- **Bug:** Ambient ``event.mod`` never sets ``KMOD_R*`` even when right
  modifier keys are held (key events themselves can be ``K_RSHIFT``).
- **Fix:** Either document "always use ``chord_matches`` / ``KMOD_SHIFT``
  groups" as the API contract, **or** track pressed modifier keys and OR
  left/right bits into subsequent events' ``mod`` (host-side or in
  ``PSDevices``/``JNDevices``).
- **Accept:** ``event.mod & KMOD_SHIFT`` true for both Shift keys on all
  backends; apps using group masks work; right-only bit checks documented
  as unsupported on browser unless tracking is added.

### H. Optional — WSLg / remote-desktop keycode notes (docs or SDL normalize)

- **Where:** comment or normalize in ``sdldisplay`` if hosts emit
  ``SDL_SCANCODE_TO_KEYCODE`` for letters (``key | 0x40000000``) instead of
  ASCII.
- **Fix:** If observed on Brad's WSLg path: normalize using
  ``SDL_GetKeyName`` → ASCII/control codes at **sdldisplay** (affects all
  consumers), not only in ``display_driver``.
- **Accept:** Letter ``KEYDOWN`` ``event.key`` in 32..126 on that host;
  ``keys.keyname`` resolves; LVGL and non-LVGL typing both work.

## What this probe prints

Interactive lines::

    KEYDOWN  key=97  keys.K_a  name='A'  mod=0x1  scancode=4  downs=1  [lv→97]

Counters expose OS repeat. ``--lvgl`` adds the mapped LVGL key. ``--selftest``
runs automated checks for A and static mapping expectations for D/E/F.
"""

import sys

_file = __file__.replace("\\", "/")
_tools = _file.rsplit("/", 1)[0] if "/" in _file else "."
_root = _tools.rsplit("/", 1)[0] if "/" in _tools else "."
_src = (_root + "/lib") if _root not in (".", "") else "lib"
_src_lib = _src + "/lib"
_src_utils = _src + "/utils"
_hw_lib = _root + "/../pydevices/lib"
# Prefer the canonical pydevices checkout for eventsys/displaydev.
for _p in (_hw_lib, _src_lib, _src_utils, _src, _tools):
    if _p and _p not in sys.path:
        sys.path.insert(0, _p)

from displaydev._domkeys import enrich_mod, key_to_keycode, mod_mask  # noqa: E402
import events  # noqa: E402
from eventsys import types  # noqa: E402
from eventsys._host import VirtualDevices  # noqa: E402
from eventsys._keypad import KeypadDevice  # noqa: E402
import keys  # noqa: E402

# ---------------------------------------------------------------------------
# Optional LVGL mapping (same function LVGL apps use)
# ---------------------------------------------------------------------------
_lv_key_from_event = None
_lv = None


def _try_import_lvgl_mapper():
    global _lv_key_from_event, _lv
    if _lv_key_from_event is not None:
        return True
    try:
        import display_driver as dd
        import lvgl as lv

        _lv_key_from_event = dd._lv_key_from_event
        _lv = lv
        return True
    except Exception:
        return False


def _lv_label(mapped):
    if _lv is None or mapped is None:
        return repr(mapped)
    for name in (
        "UP",
        "DOWN",
        "LEFT",
        "RIGHT",
        "ENTER",
        "ESC",
        "NEXT",
        "PREV",
        "BACKSPACE",
        "DEL",
        "HOME",
        "END",
    ):
        if getattr(_lv.KEY, name, None) == mapped:
            return "lv.KEY.%s" % name
    if isinstance(mapped, int) and 32 <= mapped <= 126:
        return "char %r" % chr(mapped)
    return "raw %r" % (mapped,)


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------
def _keys_const_name(code):
    for name in dir(keys):
        if name.startswith("K_") and getattr(keys, name, None) == code:
            return name
    return "?"


def _mod_parts(mod):
    if not mod:
        return "0"
    bits = []
    for name in (
        "KMOD_LSHIFT",
        "KMOD_RSHIFT",
        "KMOD_LCTRL",
        "KMOD_RCTRL",
        "KMOD_LALT",
        "KMOD_RALT",
        "KMOD_LGUI",
        "KMOD_RGUI",
        "KMOD_CAPS",
        "KMOD_NUM",
    ):
        bit = getattr(keys, name, 0)
        if bit and (mod & bit) == bit:
            bits.append(name.replace("KMOD_", ""))
    return "0x%x(%s)" % (mod, "|".join(bits) if bits else "?")


def format_key_event(event, downs=None, show_lvgl=False):
    phase = "KEYDOWN" if event.type == events.KEYDOWN else "KEYUP"
    if event.type not in (events.KEYDOWN, events.KEYUP):
        return repr(event)
    code = event.key
    parts = [
        phase,
        "key=%s" % code,
        "keys.%s" % _keys_const_name(code),
        "name=%r" % (getattr(event, "name", None) or ""),
        "mod=%s" % _mod_parts(getattr(event, "mod", 0) or 0),
        "scancode=%s" % getattr(event, "scancode", None),
    ]
    if downs is not None and event.type == events.KEYDOWN:
        parts.append("downs=%d" % downs.get(code, 0))
    if show_lvgl and _lv_key_from_event is not None:
        try:
            mapped = _lv_key_from_event(event)
            parts.append("lv→%s" % _lv_label(mapped))
        except Exception as exc:
            parts.append("lv→ERR:%s" % exc)
    # Heuristics that flag known bugs while probing
    if isinstance(code, int) and (code & 0x40000000) and _keys_const_name(code) == "?":
        parts.append("WARN:scancode-masked-unknown")
    if _keys_const_name(code) in (
        "K_LSHIFT",
        "K_RSHIFT",
        "K_LCTRL",
        "K_RCTRL",
        "K_LALT",
        "K_RALT",
        "K_LGUI",
        "K_RGUI",
    ):
        parts.append("NOTE:modifier-key")
    return "  ".join(parts)


# ---------------------------------------------------------------------------
# Self-tests (automated evidence; no display focus)
# ---------------------------------------------------------------------------
class _ProbeResult:
    def __init__(self):
        self.ok = 0
        self.fail = 0
        self.lines = []

    def check(self, name, cond, detail=""):
        if cond:
            self.ok += 1
            self.lines.append("PASS  %s" % name)
        else:
            self.fail += 1
            self.lines.append("FAIL  %s  %s" % (name, detail))


def run_selftest():
    r = _ProbeResult()

    # A — KeypadDevice must not crash on SDL-masked navigation codes
    for label, code in (
        ("K_UP", keys.K_UP),
        ("K_DOWN", keys.K_DOWN),
        ("K_LEFT", keys.K_LEFT),
        ("K_RIGHT", keys.K_RIGHT),
        ("K_ESCAPE", keys.K_ESCAPE),
    ):
        held = {code}

        def _read(h=held):
            return h

        dev = KeypadDevice(read=_read)
        try:
            out = dev.poll()
            r.check(
                "keypad_chr_safe_%s" % label,
                len(out) == 1 and out[0].type == events.KEYDOWN and out[0].key == code,
                "got %r" % (out,),
            )
        except Exception as exc:
            r.check(
                "keypad_chr_safe_%s" % label,
                False,
                "%s: %s (expected after fix A)" % (type(exc).__name__, exc),
            )

    # ASCII path still works
    held_a = {ord("a")}
    dev_a = KeypadDevice(read=lambda: held_a)
    out_a = dev_a.poll()
    r.check("keypad_ascii_a", len(out_a) == 1 and out_a[0].key == 97, repr(out_a))
    r.check(
        "keypad_up_name",
        KeypadDevice(read=lambda: {keys.K_UP}).poll()[0].name == keys.keyname(keys.K_UP),
    )

    # G — bare mod_mask stays left-only; enrich_mod adds right bits from pressed keys
    m = mod_mask(True, True, True, True)
    r.check("mod_mask_has_LSHIFT", bool(m & keys.KMOD_LSHIFT))
    r.check("mod_mask_lacks_RSHIFT", not (m & keys.KMOD_RSHIFT), "hex=%s" % hex(m))
    enriched = enrich_mod(m, {keys.K_RSHIFT, keys.K_RCTRL})
    r.check("enrich_mod_RSHIFT", bool(enriched & keys.KMOD_RSHIFT))
    r.check("enrich_mod_RCTRL", bool(enriched & keys.KMOD_RCTRL))
    r.check(
        "chord_matches_group_RCTRL",
        keys.chord_matches((keys.K_q, keys.KMOD_CTRL), keys.K_q, keys.KMOD_RCTRL),
    )
    r.check(
        "key_to_keycode_Shift_right",
        key_to_keycode("Shift", 2) == keys.K_RSHIFT,
    )

    # C — same-key KEYDOWN coalesce + KEYUP purge
    class _FakeHost:
        type = types.HOST

        def poll(self):
            return []

    vd = VirtualDevices(_FakeHost())
    kp = vd._vd_keypad
    for _ in range(5):
        kp.add_event(events.Key(events.KEYDOWN, "a", ord("a"), 0, 0, None))
    r.check("keypad_fifo_coalesce", len(kp._fifo) == 1, "len=%d" % len(kp._fifo))
    kp.add_event(events.Key(events.KEYDOWN, "b", ord("b"), 0, 0, None))
    r.check("keypad_fifo_distinct", len(kp._fifo) == 2, "len=%d" % len(kp._fifo))
    kp.add_event(events.Key(events.KEYUP, "a", ord("a"), 0, 0, None))
    r.check(
        "keypad_fifo_keyup_purge",
        len(kp._fifo) == 2 and kp._fifo[0].key == ord("b") and kp._fifo[1].type == events.KEYUP,
        "fifo=%r" % (kp._fifo,),
    )

    # D/E/F — LVGL mapper (when available)
    if _try_import_lvgl_mapper():

        class Ev:
            def __init__(self, key, mod=0, name=""):
                self.key = key
                self.mod = mod
                self.name = name

        mapped_up = _lv_key_from_event(Ev(keys.K_UP))
        r.check(
            "lv_arrows_are_caret",
            mapped_up == _lv.KEY.UP,
            "got %s" % _lv_label(mapped_up),
        )
        mapped_tab = _lv_key_from_event(Ev(keys.K_TAB))
        r.check("lv_tab_is_next", mapped_tab == _lv.KEY.NEXT, "got %s" % _lv_label(mapped_tab))
        mapped_shift = _lv_key_from_event(Ev(keys.K_LSHIFT))
        r.check("lv_modifier_dropped", mapped_shift is None, "got %r" % (mapped_shift,))
        mapped_f1 = _lv_key_from_event(Ev(keys.K_F1))
        r.check("lv_f1_dropped", mapped_f1 is None, "got %r" % (mapped_f1,))
        mapped_sa = _lv_key_from_event(Ev(keys.K_a, keys.KMOD_LSHIFT))
        r.check("lv_shift_letter", mapped_sa == ord("A"), "got %r" % (mapped_sa,))
        mapped_s1 = _lv_key_from_event(Ev(keys.K_1, keys.KMOD_LSHIFT))
        r.check("lv_shift_digit", mapped_s1 == ord("!"), "got %r" % (mapped_s1,))
        mapped_tracked = _lv_key_from_event(Ev(keys.K_a, 0), keys.KMOD_LSHIFT)
        r.check(
            "lv_tracked_mods",
            mapped_tracked == ord("A"),
            "got %r" % (mapped_tracked,),
        )
    else:
        r.lines.append("SKIP  lvgl_mapper (display_driver/lvgl not importable)")

    print("=== input_probe selftest ===")
    for line in r.lines:
        print(line)
    print("----")
    print("%d passed, %d failed" % (r.ok, r.fail))
    return 0 if r.fail == 0 else 1


# Keep in sync with the module docstring "Concrete fixes" section (MicroPython
# scripts often have ``__doc__ is None``).
_FIXES_TEXT = """
Concrete fixes required (do not implement from this file alone)

Ordered by layer. Each item is a targeted change with acceptance criteria.

A. eventsys — KeypadDevice name must not use chr(key) (multi-backend / HW)
   Where: eventsys/_keypad.py _poll
   Fix: keys.keyname(key) or "" / hex fallback — never chr(key) for arbitrary ints
   Accept: KeypadDevice(read=lambda: {keys.K_UP}).poll() returns KEYDOWN

B. displaydev — unify key-repeat policy (SDL/pygame vs browser)
   Where: sdldisplay/pgdisplay _convert vs psdisplay/jndisplay (already drop repeat)
   Fix: either drop OS repeat on desktop for parity, OR expose repeat on events.Key
        and stop silently dropping only on browser
   Accept: hold a key 2s → same KEYDOWN count on SDL and PyScript under chosen contract

C. eventsys — keypad virtual-device FIFO backpressure
   Where: eventsys/_host.py VirtualDevice.add_event (keypad fifo)
   Fix: after B — coalesce same-key KEYDOWN and/or purge on KEYUP and/or cap fifo
   Accept: hold Backspace then type — no multi-second backlog; fifo stays bounded

D. display_driver — do not feed non-text SDLKs into LVGL keypad (LVGL-only)
   Where: display_driver._lv_key_from_event / _keypad_cb
   Fix: map nav/edit keys; pass printable; skip modifiers/F-keys; sticky press state
   Accept: Shift alone never changes textarea; F1/modifiers never junk get_text()

E. display_driver — Shift/Caps for text entry (LVGL-only; after D)
   Where: _lv_key_from_event (+ optional tracked mod mask)
   Fix: apply shift map + Caps via event.mod (group-aware); track mods if mod stale
   Accept: type AbC! with Shift; Caps toggles letters

F. display_driver — arrows: focus vs caret (LVGL-only, product choice)
   Where: _lv_key_from_event (today arrows → NEXT/PREV)
   Fix: map arrows to lv.KEY.LEFT/RIGHT/UP/DOWN; keep Tab for focus
   Accept: arrows move caret in textarea; Tab still changes focus

G. eventsys — browser mod_mask left-only
   Where: eventsys/keys.py mod_mask
   Fix: document group-mask API, or track pressed modifiers into event.mod
   Accept: event.mod & KMOD_SHIFT true for both Shift keys on all backends

H. Optional — WSLg/remote-desktop letter normalization (sdldisplay if observed)
   Where: sdldisplay when letters arrive as key|0x40000000
   Fix: normalize via SDL_GetKeyName at sdldisplay (all consumers), not only LVGL
   Accept: letter event.key in 32..126 on that host
"""


def print_fixes():
    print(_FIXES_TEXT.strip())


# ---------------------------------------------------------------------------
# Interactive host probe
# ---------------------------------------------------------------------------
def run_interactive(show_lvgl=False):
    if show_lvgl:
        if not _try_import_lvgl_mapper():
            print("WARN: --lvgl requested but display_driver/lvgl unavailable")
            show_lvgl = False
        else:
            print("LVGL mapper: display_driver._lv_key_from_event")
        from display_driver import runtime
    else:
        from app_runtime import runtime

    downs = {}
    pressed = set()
    fifo_note = {"last_warn": 0}

    def _on_key(event):
        if event.type == events.KEYDOWN:
            downs[event.key] = downs.get(event.key, 0) + 1
            pressed.add(event.key)
        elif event.type == events.KEYUP:
            pressed.discard(event.key)
        print(format_key_event(event, downs=downs, show_lvgl=show_lvgl))
        # Chord sample: Ctrl+Shift+letter
        mod = getattr(event, "mod", 0) or 0
        if event.type == events.KEYDOWN and (mod & keys.KMOD_CTRL) and (mod & keys.KMOD_SHIFT):
            print(
                "  chord: Ctrl+Shift+%s  chord_matches(Ctrl)=%s"
                % (
                    _keys_const_name(event.key),
                    keys.chord_matches((event.key, keys.KMOD_CTRL), event.key, mod),
                )
            )

    def _tick(_=None):
        # If LVGL VirtualDevices exist, report keypad fifo depth (fix C).
        try:
            from eventsys._host import _vd_peers

            for host in runtime.devices:
                if getattr(host, "type", None) != types.HOST:
                    continue
                peers = _vd_peers.get(id(host)) or []
                for vd in peers:
                    depth = len(vd._vd_keypad._fifo)
                    if depth >= 8 and depth != fifo_note["last_warn"]:
                        print("WARN keypad_fifo_depth=%d (fix C backlog)" % depth)
                        fifo_note["last_warn"] = depth
        except Exception:
            pass

    print("input_probe: focus the display window, then press keys.")
    print("Watch downs= for OS key-repeat. Modifiers show NOTE:modifier-key.")
    print("Try: letters, Shift+letter, Shift+1, arrows, Tab, Backspace hold, Ctrl+Q quit.")
    print("held keys / down counts update live.\n")

    for et in (events.KEYDOWN, events.KEYUP):
        runtime.on(et, _on_key)
    runtime.on_tick(_tick, period=200, async_=False)
    runtime.run_forever()


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--fixes" in argv:
        print_fixes()
        return 0
    if "--selftest" in argv:
        if "--lvgl" in argv:
            _try_import_lvgl_mapper()
        return run_selftest()
    show_lvgl = "--lvgl" in argv
    run_interactive(show_lvgl=show_lvgl)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(0) from None
