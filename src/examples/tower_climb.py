# multimer types: all
# pyscript binaries: assets/climber.bmp, assets/tower_tiles.bmp, assets/tower_bg.bmp
"""
tower_climb.py — 1980s-style vertical scrolling platformer.

Climb a magical tree toward the clouds, inspired by Ice Climber, Nebulus,
Magical Tree, and Crazy Climber.  Uses software vertical scrolling (no
hardware ``vscsad`` / rotation tricks) so it runs on PGDisplay and SDLDisplay.

Layout scales from the 320×480 reference to taller panels (480×800, 720×720, …).
Built from the four core pydisplay libraries only.
"""

from collections import namedtuple

from board_config import broker, display_drv
from displaysys import color565
from eventsys import poll_quit_discarding_others
from eventsys.keys import Keys
from graphics import BMP565, FrameBuffer, RGB565, rect, text8
from multimer import sleep_ms
from tower_climb_trace import open_trace

try:
    from random import getrandbits, randint
except ImportError:

    def getrandbits(n):
        return 0

    def randint(a, b):
        return a


try:
    from time import ticks_diff, ticks_ms
except ImportError:
    from multimer import ticks_diff, ticks_ms


# --- Scalable layout (reference 320×480) -------------------------------------------------------

REF_W, REF_H = 320, 480


class Layout:
    __slots__ = ("w", "h", "sw", "sh", "s", "field_w", "ox")

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.sw = w / REF_W
        self.sh = h / REF_H
        self.s = min(self.sw, self.sh)
        self.field_w = min(w, max(self.x(REF_W), self.x(280)))
        self.ox = (w - self.field_w) // 2

    def x(self, n):
        return int(n * self.sw)

    def y(self, n):
        return int(n * self.sh)

    def u(self, n):
        return max(1, int(n * self.s))


L = Layout(display_drv.width, display_drv.height)

if display_drv.requires_byteswap:
    needs_swap = display_drv.disable_auto_byteswap(True)
else:
    needs_swap = False


def _c(r, g, b):
    v = color565(r, g, b)
    if needs_swap:
        v = ((v & 0xFF) << 8) | (v >> 8)
    return v


HUD_BG = _c(16, 20, 48)
HUD_INK = _c(255, 248, 200)
PARTICLE = _c(255, 200, 60)

# --- Assets ------------------------------------------------------------------------------------

CLIMBER = BMP565("examples/assets/climber.bmp", streamed=True)
TILES = BMP565("examples/assets/tower_tiles.bmp", streamed=True)
BG = BMP565("examples/assets/tower_bg.bmp", streamed=True)

SPR_W = CLIMBER.width // 4
SPR_H = CLIMBER.height // 3
SPR_KEY = CLIMBER[0]
TILE = 16

T_BARK, T_BRANCH_L, T_BRANCH_R, T_ICE, T_LEAF, T_GEM, T_SPIKE, T_CLOUD = range(8)

# --- Level helpers -----------------------------------------------------------------------------

Rect = namedtuple("Rect", "x y w h kind")
Point = namedtuple("Point", "x y")


def _tile_rect(idx):
    col = idx % 8
    row = idx // 8
    return col * TILE, row * TILE


def _blit_tile(idx, dx, dy, repeat=1):
    sx, sy = _tile_rect(idx)
    buf = TILES[sx : sx + TILE, sy : sy + TILE]
    for i in range(repeat):
        display_drv.blit_rect(buf, dx + i * TILE, dy, TILE, TILE)


def _draw_sprite(pose, frame, dx, dy):
    col = frame % 4
    buf = CLIMBER[col * SPR_W : (col + 1) * SPR_W, pose * SPR_H : (pose + 1) * SPR_H]
    display_drv.blit_transparent(buf, dx, dy, SPR_W, SPR_H, SPR_KEY)


def _build_level():
    """Procedural tower: branches, ice, gems, hazards."""
    plats = []
    gems = []
    hazards = []
    trunk = L.field_w // 2
    y = L.y(REF_H - 80)
    top = L.y(120)
    step = L.y(52)
    n = 0
    while y > top:
        side = -1 if n % 2 else 1
        bw = L.x(56 + (n % 3) * 12)
        bx = trunk + side * L.x(36 + (n % 4) * 8) - bw // 2
        bx = max(L.ox + L.u(4), min(bx, L.ox + L.field_w - bw - L.u(4)))
        kind = T_BRANCH_L if side < 0 else T_BRANCH_R
        if n % 5 == 2:
            kind = T_ICE
        elif n % 7 == 4:
            kind = T_LEAF
        plats.append(Rect(bx, y, bw, TILE, kind))
        if n % 3 == 1:
            gems.append(Point(bx + bw // 2 - 6, y - 18))
        if n % 6 == 0 and n > 0:
            hazards.append([bx + bw // 2, y - L.y(200), 10, 0.0, L.y(2.2)])
        y -= step + (n % 4) * L.u(6)
        n += 1
    plats.append(Rect(L.ox + L.field_w // 2 - L.x(40), L.y(REF_H - 48), L.x(80), TILE, T_BARK))
    goal_y = top - L.y(20)
    return plats, gems, hazards, goal_y


PLATFORMS, GEMS, HAZARDS, GOAL_Y = _build_level()

_trace = open_trace()

# --- Background draw ---------------------------------------------------------------------------


def _draw_bg(camera_y):
    """Blit a slice of the parallax strip; stretch when field width != asset width."""
    cy = max(0, min(-int(camera_y), BG.height - 1))
    slice_h = min(L.h, BG.height - cy)
    if L.field_w == BG.width:
        display_drv.blit_rect(BG[0:BG.width, cy : cy + slice_h], L.ox, 0, L.field_w, slice_h)
        if slice_h < L.h:
            display_drv.fill_rect(L.ox, slice_h, L.field_w, L.h - slice_h, _c(8, 12, 40))
    else:
        for col in range(L.field_w):
            sx = col * BG.width // L.field_w
            chunk = BG[sx : sx + 1, cy : cy + slice_h]
            display_drv.blit_rect(chunk, L.ox + col, 0, 1, slice_h)
        if slice_h < L.h:
            display_drv.fill_rect(L.ox, slice_h, L.field_w, L.h - slice_h, _c(8, 12, 40))
    if L.ox > 0:
        display_drv.fill_rect(0, 0, L.ox, L.h, _c(4, 8, 28))
    if L.ox + L.field_w < L.w:
        display_drv.fill_rect(L.ox + L.field_w, 0, L.w - L.ox - L.field_w, L.h, _c(4, 8, 28))


# --- Physics -----------------------------------------------------------------------------------

GRAVITY = 0.55
JUMP_V = -9.0
MAX_FALL = 11.0
MOVE_A = 0.7
MAX_RUN = 4.5
FRICTION = 0.82
ANCHOR_Y = L.y(300)


class Player:
    __slots__ = ("x", "y", "vx", "vy", "on_ground", "coyote", "jump_buf", "lives", "score", "pose")

    def __init__(self):
        self.x = float(L.ox + L.field_w // 2 - SPR_W // 2)
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.coyote = 8
        self.jump_buf = 0
        self.lives = 3
        self.score = 0
        self.pose = 2


def _hitbox(p):
    m = 6
    return Rect(int(p.x + m), int(p.y + 10), SPR_W - m * 2, SPR_H - 12, 0)


def _overlap(a, b):
    return a.x < b.x + b.w and a.x + a.w > b.x and a.y < b.y + b.h and a.y + a.h > b.y


def _resolve_x(p, plat, dx):
    box = _hitbox(p)
    if not _overlap(box, plat):
        return None
    old_x = p.x
    if dx > 0:
        p.x = plat.x - (SPR_W - 6)
    elif dx < 0:
        p.x = plat.x + plat.w - 6
    else:
        return None
    if _trace is not None:
        _trace.log_resolve_x(p, plat, dx, old_x)
    return plat


def _nearby_platforms(hitbox, player_y, plats, radius=96):
    nearby = []
    for plat in plats:
        if plat.kind == T_GEM:
            continue
        if hitbox.x + hitbox.w <= plat.x or hitbox.x >= plat.x + plat.w:
            continue
        if abs(plat.y - (player_y + SPR_H)) <= radius:
            nearby.append(plat)
    return nearby


def _land(p, prev_y, plats):
    p.on_ground = False
    if p.vy < 0:
        return None
    feet = int(p.y + SPR_H - 4)
    prev_feet = int(prev_y + SPR_H - 4)
    box = _hitbox(p)
    best = None
    best_plat = None
    for plat in plats:
        if plat.kind == T_GEM:
            continue
        if box.x + box.w <= plat.x or box.x >= plat.x + plat.w:
            continue
        top = plat.y
        if prev_feet <= top <= feet and (best is None or top > best):
            best = top
            best_plat = plat
    if best is not None:
        p.y = best - SPR_H
        p.vy = 0
        p.on_ground = True
        if _trace is not None:
            result = "hurt" if best_plat.kind == T_SPIKE else "land"
            _trace.log_land(p, prev_y, best_plat, result, feet)
        if best_plat.kind == T_SPIKE:
            return "hurt"
    return None


def _ground_platform(plats):
    best = None
    for plat in plats:
        if plat.kind == T_GEM:
            continue
        if best is None or plat.y > best.y:
            best = plat
    return best


def _snap_to_ground(p, plats, reason="spawn"):
    plat = _ground_platform(plats)
    if plat is None:
        return
    p.y = float(plat.y - SPR_H)
    p.vx = p.vy = 0.0
    p.on_ground = True
    p.coyote = 8
    p.jump_buf = 0
    if _trace is not None:
        _trace.log_snap(reason, p, plat)


# --- Input -------------------------------------------------------------------------------------

_keys = {"left": False, "right": False, "up": False, "down": False, "smash": False}


def _handle_event(ev):
    t = ev.type
    if t == broker.events.KEYDOWN:
        k = ev.key
        if k in (Keys.K_LEFT, Keys.K_a):
            _keys["left"] = True
        elif k in (Keys.K_RIGHT, Keys.K_d):
            _keys["right"] = True
        elif k in (Keys.K_SPACE, Keys.K_UP, Keys.K_w):
            _keys["up"] = True
        elif k in (Keys.K_DOWN, Keys.K_s):
            _keys["down"] = True
            _keys["smash"] = True
        elif k in (Keys.K_x, Keys.K_z):
            _keys["smash"] = True
        if _trace is not None:
            _trace.log_input("keydown", key=int(k))
    elif t == broker.events.KEYUP:
        k = ev.key
        if k in (Keys.K_LEFT, Keys.K_a):
            _keys["left"] = False
        elif k in (Keys.K_RIGHT, Keys.K_d):
            _keys["right"] = False
        elif k in (Keys.K_SPACE, Keys.K_UP, Keys.K_w):
            _keys["up"] = False
        elif k in (Keys.K_DOWN, Keys.K_s):
            _keys["down"] = False
            _keys["smash"] = False
        if _trace is not None:
            _trace.log_input("keyup", key=int(k))
    elif t == broker.events.MOUSEBUTTONDOWN:
        tx, ty = ev.pos
        if ty < L.h // 3:
            _keys["up"] = True
        elif ty > 2 * L.h // 3:
            _keys["smash"] = True
        elif tx < L.w // 2:
            _keys["left"] = True
        else:
            _keys["right"] = True
        if _trace is not None:
            _trace.log_input("mousedown", pos=[tx, ty], keys=dict(_keys))
    elif t == broker.events.MOUSEBUTTONUP:
        _keys["left"] = _keys["right"] = _keys["up"] = _keys["smash"] = False
        if _trace is not None:
            _trace.log_input("mouseup", keys=dict(_keys))


_particles = []


def _spark(x, y, n=6):
    for _ in range(n):
        _particles.append(
            [x + randint(-6, 6), y + randint(-4, 4), randint(-3, 3), randint(6, 14)]
        )


# --- HUD & overlays ----------------------------------------------------------------------------

_hud_h = L.u(16)
_hud_buf = bytearray(L.w * _hud_h * 2)
_hud_fb = FrameBuffer(_hud_buf, L.w, _hud_h, RGB565)

_overlay_h = L.y(220)
_overlay_buf = bytearray(L.w * _overlay_h * 2)
_overlay_fb = FrameBuffer(_overlay_buf, L.w, _overlay_h, RGB565)

SPLASH_LINES = (
    "TOWER CLIMB",
    "",
    "Climb the magical tree",
    "to the summit!",
    "",
    "Move: arrows / A D",
    "Jump: Space / W / tap top",
    "Smash ice: Down / S",
    "",
    "Collect gems, break ice,",
    "dodge falling debris.",
    "",
    "Press any key or tap",
    "to start",
)


def _draw_hud(p, altitude):
    display_drv.fill_rect(0, 0, L.w, _hud_h, HUD_BG)
    pct = min(99, altitude * 100 // max(1, L.y(REF_H - 80) - GOAL_Y))
    msg = f"SCORE {p.score:04d}  M {pct:2d}%  LIVES {p.lives}"
    _hud_fb.fill(HUD_BG)
    text8(_hud_fb, msg, L.u(4), L.u(3), HUD_INK)
    display_drv.blit_rect(_hud_buf, 0, 0, L.w, _hud_h)


def _skip_ui():
    try:
        import pydisplay_test_mode

        return pydisplay_test_mode.ENABLED
    except ImportError:
        return False


def _draw_text_panel(lines, y0=None):
    if y0 is None:
        y0 = max(0, (L.h - _overlay_h) // 2)
    panel_c = _c(12, 16, 40)
    border_c = _c(255, 180, 40)
    title_c = _c(255, 220, 80)
    x0 = L.u(8)
    pw = L.w - L.u(16)
    display_drv.fill_rect(x0, y0, pw, _overlay_h, panel_c)
    rect(display_drv, x0, y0, pw, _overlay_h, border_c)
    _overlay_fb.fill(panel_c)
    ty = 10
    for i, line in enumerate(lines):
        if line:
            color = title_c if i == 0 else HUD_INK
            text8(_overlay_fb, line, 10, ty, color)
        ty += 12
    display_drv.blit_rect(_overlay_buf, 0, y0, L.w, _overlay_h)


def _is_start_input(ev):
    if ev.type == broker.events.KEYDOWN:
        return True
    if ev.type == broker.events.MOUSEBUTTONDOWN:
        return True
    return False


def _wait_for_input(draw_fn=None):
    """Block until the user taps or presses a key (splash / life lost)."""
    if _skip_ui():
        if draw_fn is not None:
            draw_fn()
            display_drv.show()
        return True
    while True:
        if poll_quit_discarding_others(broker):
            return False
        if draw_fn is not None:
            draw_fn()
            display_drv.show()
        for ev in broker.poll():
            if _is_start_input(ev):
                _keys["left"] = _keys["right"] = _keys["up"] = _keys["down"] = False
                _keys["smash"] = False
                return True
        sleep_ms(0)
        sleep_ms(16)


def _show_splash():
    def draw():
        _draw_bg(0)
        _draw_text_panel(SPLASH_LINES)

    return _wait_for_input(draw)


def _life_lost_pause(player):
    lines = (
        "LIFE LOST!",
        "",
        f"Lives left: {player.lives}",
        "",
        "Press any key or tap",
        "to continue",
    )

    def draw():
        _draw_bg(0)
        _draw_text_panel(lines)

    return _wait_for_input(draw)


# --- Main --------------------------------------------------------------------------------------


def _respawn(p, plats):
    p.lives -= 1
    p.x = float(L.ox + L.field_w // 2 - SPR_W // 2)
    _snap_to_ground(p, plats, reason="respawn")


def _lose_life(player, camera_ref, plats, reason="unknown"):
    if _trace is not None:
        _trace.log_life(reason, player, camera_ref[0])
    _respawn(player, plats)
    camera_ref[0] = 0.0
    if player.lives <= 0:
        return False
    return _life_lost_pause(player)


def _take_over_display_refresh():
    sub = getattr(broker, "display_refresh", None)
    if sub is not None:
        sub.deinit()
        broker.display_refresh = None


def _restore_display_refresh():
    if getattr(broker, "display_refresh", None) is None:
        from board_config import _wire_display_refresh

        _wire_display_refresh(broker, display_drv)


def _run_game(show_splash=True):
    _take_over_display_refresh()
    if _trace is not None:
        _trace.log_init(L, SPR_W, SPR_H, PLATFORMS, GEMS, HAZARDS, GOAL_Y)
        show_splash = False
    try:
        if show_splash and not _skip_ui():
            if not _show_splash():
                return
            if poll_quit_discarding_others(broker):
                return

        while True:
            player = Player()
            plats = list(PLATFORMS)
            _snap_to_ground(player, plats, reason="round_start")
            gems = list(GEMS)
            hazards = [list(h) for h in HAZARDS]
            camera = 0.0
            frame = 0
            won = False
            _particles.clear()

            while player.lives > 0 and not won:
                if poll_quit_discarding_others(broker):
                    return

                for ev in broker.poll():
                    _handle_event(ev)

                frame += 1

                # Camera follows upward climbs (software scroll).
                target_cam = player.y - ANCHOR_Y
                if target_cam < camera:
                    camera = target_cam
                if camera < 0:
                    camera = 0

                # Input
                if _keys["left"]:
                    player.vx -= MOVE_A
                    player.pose = 0
                if _keys["right"]:
                    player.vx += MOVE_A
                    player.pose = 0
                if not _keys["left"] and not _keys["right"] and player.on_ground:
                    player.pose = 2
                if _keys["up"]:
                    player.jump_buf = 8
                else:
                    player.jump_buf = max(0, player.jump_buf - 1)

                if player.on_ground:
                    player.coyote = 8
                else:
                    player.coyote = max(0, player.coyote - 1)
                    player.pose = 1

                if player.jump_buf and player.coyote:
                    player.vy = JUMP_V * (L.s if L.s < 1.2 else 1.0)
                    player.on_ground = False
                    player.coyote = 0
                    player.jump_buf = 0
                    _spark(int(player.x + SPR_W // 2), int(player.y + SPR_H), 4)

                # Smash ice (Ice Climber mallet)
                if _keys["smash"] and player.on_ground:
                    box = _hitbox(player)
                    for i, plat in enumerate(plats):
                        if plat.kind == T_ICE and _overlap(
                            box, Rect(plat.x, plat.y - 4, plat.w, plat.h + 8, T_ICE)
                        ):
                            plats[i] = Rect(plat.x, plat.y, plat.w, plat.h, T_BRANCH_L)
                            player.score += 15
                            _spark(plat.x + plat.w // 2, plat.y, 10)
                            break

                player.vx = max(-MAX_RUN, min(MAX_RUN, player.vx))
                if player.on_ground:
                    player.vx *= FRICTION
                else:
                    player.vx *= 0.99
                if not player.on_ground:
                    player.vy = min(MAX_FALL, player.vy + GRAVITY)

                ox = player.x
                player.x += player.vx
                x_blocked = []
                for plat in plats:
                    blocked = _resolve_x(player, plat, player.x - ox)
                    if blocked is not None:
                        x_blocked.append(blocked)

                oy = player.y
                player.y += player.vy
                hurt = _land(player, oy, plats)
                cam_box = [camera]
                if hurt:
                    if not _lose_life(player, cam_box, plats, reason="spike"):
                        break
                    camera = cam_box[0]
                    continue

                # Fall below start
                if player.y > L.y(REF_H) + L.u(40):
                    if not _lose_life(player, cam_box, plats, reason="fall"):
                        break
                    camera = cam_box[0]
                    continue

                # Gems
                box = _hitbox(player)
                got = []
                for i, g in enumerate(gems):
                    gr = Rect(g.x, g.y, 12, 12, T_GEM)
                    if _overlap(box, gr):
                        got.append(i)
                        player.score += 25
                        _spark(g.x, g.y, 6)
                for i in reversed(got):
                    gems.pop(i)

                # Hazards (Crazy Climber drops)
                if frame % 90 == 0 and player.y < L.y(REF_H - 100):
                    hx = L.ox + randint(20, max(21, L.field_w - 20))
                    hazards.append([hx, camera - 20, 10, 0.0, L.y(2.5)])
                life_lost = False
                for hz in hazards:
                    hz[1] += hz[4]
                    hz[3] += 0.05
                    hr = Rect(int(hz[0]), int(hz[1]), hz[2], hz[2], T_SPIKE)
                    if _overlap(box, hr):
                        if not _lose_life(player, cam_box, plats, reason="hazard"):
                            life_lost = True
                            break
                        camera = cam_box[0]
                        life_lost = True
                        break
                if life_lost and player.lives <= 0:
                    break
                if life_lost:
                    continue
                hazards[:] = [h for h in hazards if h[1] < camera + L.h + L.u(40)]

                if player.y <= GOAL_Y:
                    won = True
                    player.score += 500

                if _trace is not None:
                    _trace.frame += 1
                    box = _hitbox(player)
                    feet = int(player.y + SPR_H - 4)
                    nearby = _nearby_platforms(box, player.y, plats)
                    _trace.log_frame(
                        player,
                        camera,
                        _keys,
                        box,
                        feet,
                        (int(player.x), int(player.y), SPR_W, SPR_H),
                        nearby,
                        x_blocked,
                    )

                altitude = int(L.y(REF_H - 80) - player.y)
                _draw_bg(camera)
                cam = int(camera)

                # Platforms
                for plat in plats:
                    sy = int(plat.y - cam)
                    if sy < -TILE or sy > L.h:
                        continue
                    if plat.kind == T_BARK:
                        reps = max(1, plat.w // TILE)
                        _blit_tile(T_BARK, plat.x, sy, reps)
                    elif plat.kind in (T_BRANCH_L, T_BRANCH_R, T_ICE, T_LEAF):
                        reps = max(1, plat.w // TILE)
                        _blit_tile(plat.kind, plat.x, sy, reps)

                # Gems
                for g in gems:
                    sy = int(g.y - cam)
                    if 0 <= sy < L.h:
                        _blit_tile(T_GEM, g.x, sy)

                # Hazards
                for hz in hazards:
                    sy = int(hz[1] - cam)
                    if 0 <= sy < L.h:
                        _blit_tile(T_SPIKE, int(hz[0]), sy)

                # Particles
                live = []
                for px, py, pvx, life in _particles:
                    life -= 1
                    if life > 0:
                        px += pvx
                        py += 1
                        sy = int(py - cam)
                        if 0 <= sy < L.h:
                            display_drv.pixel(int(px), sy, PARTICLE)
                        live.append([px, py, pvx, life])
                _particles[:] = live

                _draw_sprite(player.pose, frame // 5, int(player.x), int(player.y - cam))
                _draw_hud(player, altitude)

                display_drv.show()
                sleep_ms(0)
                sleep_ms(16)

            # End of round — game over or win
            msg = "SUMMIT!" if won else "GAME OVER"
            lines = (
                msg,
                "SCORE %04d" % player.score,
                "",
                "Press any key or tap",
                "to play again",
            )

            def draw_end():
                _draw_bg(camera)
                _draw_text_panel(lines)

            if not _wait_for_input(draw_end):
                break
            # Replay: skip splash on next round
            show_splash = False

    finally:
        CLIMBER.deinit()
        TILES.deinit()
        BG.deinit()
        _restore_display_refresh()
        if _trace is not None:
            _trace.close()


def main():
    _run_game(show_splash=True)


main()
