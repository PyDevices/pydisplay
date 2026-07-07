# multimer types: all
# pyscript binaries: assets/runner.bmp, assets/longstreet.bmp
"""
platformer.py — side-scrolling platformer for ILI9341-class displays.

Uses hardware vertical scrolling with ``display_drv.rotation = 90`` so the
viewport scrolls horizontally (see ``bmp565_scroll_sprite.py``).  Built only
from the four core pydisplay libraries: ``displaysys``, ``graphics``,
``eventsys``, and ``multimer``.
"""

from collections import namedtuple

from board_config import broker, display_drv
from displaysys import alloc_buffer, color565
from eventsys import poll_quit_discarding_others
from eventsys.keys import Keys
from graphics import BMP565, FrameBuffer, RGB565, text8
from multimer import sleep_ms

try:
    from random import getrandbits
except ImportError:

    def getrandbits(n):
        return 0


try:
    from time import ticks_diff, ticks_ms
except ImportError:
    from multimer import ticks_diff, ticks_ms


# --- Display setup (ILI9341 landscape via 90° rotation) -----------------------------------------

display_drv.rotation = 90
WIDTH = display_drv.width
HEIGHT = display_drv.height

if display_drv.requires_byteswap:
    needs_swap = display_drv.disable_auto_byteswap(True)
else:
    needs_swap = False


def _c(r, g, b):
    c = color565(r, g, b)
    if needs_swap:
        c = ((c & 0xFF) << 8) | (c >> 8)
    return c


# Palette
SKY_TOP = _c(0x18, 0x10, 0x48)
SKY_BOT = _c(0xE8, 0x58, 0x28)
SUN = _c(0xFF, 0xE0, 0x60)
MOUNTAIN_FAR = _c(0x30, 0x28, 0x58)
MOUNTAIN_NEAR = _c(0x48, 0x38, 0x68)
CLOUD = _c(0xF0, 0xE8, 0xFF)
GRASS = _c(0x30, 0xC0, 0x40)
GRASS_HI = _c(0x60, 0xF0, 0x70)
DIRT = _c(0x88, 0x58, 0x28)
STONE = _c(0x90, 0x90, 0xA8)
STONE_HI = _c(0xC8, 0xD0, 0xE8)
CRYSTAL = _c(0x40, 0xE8, 0xFF)
CRYSTAL_GLOW = _c(0xA0, 0xFF, 0xFF)
SPIKE = _c(0xF0, 0x40, 0x60)
COIN_COLORS = (_c(0xFF, 0xD0, 0x20), _c(0xFF, 0xF0, 0x80), _c(0xFF, 0xA0, 0x10))
HUD_BG = _c(0x10, 0x10, 0x20)
HUD_INK = _c(0xFF, 0xF8, 0xE0)
PARTICLE = _c(0xFF, 0xC0, 0x60)

TILE = 16
SKY_ROWS = 96
PLAYER_SCREEN_X = 72

# --- Assets -------------------------------------------------------------------------------------

try:
    _parallax = BMP565("examples/assets/longstreet.bmp", streamed=True, mirrored=True)
    _has_parallax = True
except OSError:
    _parallax = None
    _has_parallax = False

_runner = BMP565("examples/assets/runner.bmp", streamed=True)
RUN_W = _runner.width // 6
RUN_H = _runner.height // 3
_run_frames = [namedtuple("pt", "x y")(i * RUN_W, 0) for i in range(6)]
_jump_frames = [namedtuple("pt", "x y")(i * RUN_W, RUN_H * 2) for i in range(2)]
_sprite_bg = _runner[0]

# --- Tile graphics ------------------------------------------------------------------------------

_TILE_STYLES = ("grass", "dirt", "stone", "crystal", "spike")
_tile_bufs = {}


def _make_tile(style):
    buf = alloc_buffer(TILE * TILE * 2)
    for y in range(TILE):
        for x in range(TILE):
            if style == "grass":
                if y == 0:
                    c = GRASS_HI if (x & 1) == (y & 1) else GRASS
                elif y < 5:
                    c = GRASS if x % 3 else GRASS_HI
                else:
                    c = DIRT if y > 10 else GRASS
            elif style == "dirt":
                c = DIRT
                if (x + y) % 5 == 0:
                    c = _c(0x70, 0x48, 0x20)
            elif style == "stone":
                edge = x == 0 or y == 0 or x == TILE - 1 or y == TILE - 1
                c = STONE_HI if edge else STONE
                if (x + y) % 4 == 0 and not edge:
                    c = _c(0x70, 0x78, 0x90)
            elif style == "crystal":
                edge = x == 0 or y == 0 or x == TILE - 1 or y == TILE - 1
                c = CRYSTAL_GLOW if edge else CRYSTAL
                if x == y or x + y == TILE - 1:
                    c = CRYSTAL_GLOW
            else:  # spike
                c = STONE
                mid = TILE // 2
                if abs(x - mid) <= y // 2:
                    c = SPIKE
            idx = (y * TILE + x) * 2
            buf[idx] = c & 0xFF
            buf[idx + 1] = c >> 8
    return buf


for _style in _TILE_STYLES:
    _tile_bufs[_style] = _make_tile(_style)


def _blit_tile(dest_x, dest_y, style):
    display_drv.blit_rect(_tile_bufs[style], dest_x, dest_y, TILE, TILE)


# --- Level data ---------------------------------------------------------------------------------

Point = namedtuple("Point", "x y")
Rect = namedtuple("Rect", "x y w h style")

# Hand-tuned platforms (world coordinates).  Ground baseline near y=192.
PLATFORMS = [
    Rect(0, 192, 520, 48, "grass"),
    Rect(560, 176, 96, 16, "stone"),
    Rect(720, 144, 80, 16, "crystal"),
    Rect(880, 160, 112, 16, "stone"),
    Rect(1080, 128, 96, 16, "crystal"),
    Rect(1240, 176, 128, 16, "grass"),
    Rect(1440, 144, 80, 16, "stone"),
    Rect(1580, 112, 96, 16, "crystal"),
    Rect(1740, 160, 160, 16, "grass"),
    Rect(1960, 128, 96, 16, "stone"),
    Rect(2120, 96, 80, 16, "crystal"),
    Rect(2280, 160, 200, 16, "grass"),
    Rect(2540, 144, 96, 16, "stone"),
    Rect(2700, 112, 112, 16, "crystal"),
    Rect(2880, 176, 240, 48, "grass"),
]

SPIKES = [
    Rect(640, 208, 48, 16, "spike"),
    Rect(1000, 208, 64, 16, "spike"),
    Rect(1520, 208, 48, 16, "spike"),
    Rect(2060, 208, 64, 16, "spike"),
]

WORLD_END = 3100
CHECKPOINTS = (0, 1240, 2280, 2880)


def _coins_for_level():
    coins = []
    for plat in PLATFORMS:
        if plat.style == "spike":
            continue
        step = 24
        cx = plat.x + 12
        while cx < plat.x + plat.w - 8:
            cy = plat.y - 18
            coins.append(Point(cx, cy))
            cx += step
    return coins


COINS = _coins_for_level()


class Enemy:
    __slots__ = ("x", "y", "w", "h", "x0", "x1", "dx", "hue")

    def __init__(self, x, y, x1, hue=0):
        self.x = x
        self.y = y
        self.w = 20
        self.h = 16
        self.x0 = x
        self.x1 = x1
        self.dx = 1
        self.hue = hue


ENEMIES = [
    Enemy(600, 160, 680),
    Enemy(920, 144, 1020, 1),
    Enemy(1300, 160, 1420, 2),
    Enemy(1800, 128, 1920, 1),
    Enemy(2400, 144, 2520, 0),
    Enemy(2760, 96, 2860, 2),
]


# --- Parallax / sky column renderer -------------------------------------------------------------

_col_buf = alloc_buffer(HEIGHT * 2)


def _sky_color(y):
    if y >= SKY_ROWS:
        return 0
    t = y * 255 // max(SKY_ROWS - 1, 1)
    r1, g1, b1 = (SKY_TOP >> 8) & 0xF8, (SKY_TOP >> 3) & 0xFC, (SKY_TOP << 3) & 0xF8
    r2, g2, b2 = (SKY_BOT >> 8) & 0xF8, (SKY_BOT >> 3) & 0xFC, (SKY_BOT << 3) & 0xF8
    r = r1 + (r2 - r1) * t // 255
    g = g1 + (g2 - g1) * t // 255
    b = b1 + (b2 - b1) * t // 255
    return (r & 0xF8) << 8 | (g & 0xFC) << 3 | (b & 0xF8) >> 3


def _mountain_height(world_x, scale, base):
    return int(base + 28 * ((world_x * scale // 97) % 7) + 18 * ((world_x * scale // 53) % 5))


def _star_at(world_x, y):
    if y > 72:
        return False
    return ((world_x * 73 + y * 131) % 229) < 3


def _fill_column_buffer(world_x, fast=False):
    far = _mountain_height(world_x, 3, 40)
    near = _mountain_height(world_x, 7, 64)
    sun_x = 220
    sun_r = 22
    for y in range(HEIGHT):
        if y < SKY_ROWS:
            c = _sky_color(y)
            if _star_at(world_x, y):
                c = HUD_INK
            dx = world_x - sun_x
            if dx * dx + (y - 36) * (y - 36) < sun_r * sun_r:
                c = SUN
            elif y >= SKY_ROWS - far:
                c = MOUNTAIN_FAR
            elif y >= SKY_ROWS - near:
                c = MOUNTAIN_NEAR
            elif ((world_x // 40 + y // 18) % 11) == 0 and 24 < y < 60:
                c = CLOUD
        else:
            c = 0
        idx = y * 2
        _col_buf[idx] = c & 0xFF
        _col_buf[idx + 1] = c >> 8
    if not fast and _has_parallax:
        col = world_x % _parallax.height
        chunk = _parallax[col : col + 1]
        # Blend parallax into lower sky / horizon band.
        for y in range(48, SKY_ROWS + 32):
            if y >= HEIGHT:
                break
            idx = y * 2
            px = chunk[0] | (chunk[1] << 8)
            if px != 0:
                _col_buf[idx] = chunk[0]
                _col_buf[idx + 1] = chunk[1]


def _draw_bg_column(screen_x, world_x, fast=False):
    _fill_column_buffer(world_x, fast=fast)
    display_drv.blit_rect(_col_buf, screen_x, 0, 1, HEIGHT)


def _tile_at(world_x, world_y):
    for rect in SPIKES:
        if rect.x <= world_x < rect.x + rect.w and rect.y <= world_y < rect.y + rect.h:
            return "spike"
    for plat in PLATFORMS:
        if plat.x <= world_x < plat.x + plat.w and plat.y <= world_y < plat.y + plat.h:
            return plat.style
    return None


def _floor_y_at(world_x):
    best = HEIGHT + 100
    for rect in PLATFORMS + SPIKES:
        if rect.x <= world_x < rect.x + rect.w:
            top = rect.y
            if top < best:
                best = top
    return best


def _screen_x(world_x, camera, scroll):
    return (int(world_x) - camera + scroll) % WIDTH


def _world_x(screen_x, camera, scroll):
    return camera + screen_x - scroll


def _draw_terrain_column(screen_x, world_x):
    for plat in PLATFORMS + SPIKES:
        if plat.x <= world_x < plat.x + plat.w:
            ty = plat.y // TILE
            th = (plat.h + TILE - 1) // TILE
            for tyi in range(ty, ty + th):
                wy = tyi * TILE
                if plat.y <= wy < plat.y + plat.h:
                    _blit_tile(screen_x, wy, plat.style)


def _restore_rect(sx, y, w, h, camera, scroll):
    """Redraw parallax + terrain under a dynamic sprite."""
    x0 = max(0, sx)
    x1 = min(WIDTH, sx + w)
    for col in range(x0, x1):
        wx = _world_x(col, camera, scroll)
        _draw_bg_column(col, wx)
        _draw_terrain_column(col, wx)
    if y < SKY_ROWS:
        return
    for plat in PLATFORMS + SPIKES:
        psx = _screen_x(plat.x, camera, scroll)
        if psx + plat.w < x0 or psx > x1:
            continue
        tx0 = max(0, (x0 - psx) // TILE)
        tx1 = (x1 - psx + TILE - 1) // TILE
        for txi in range(tx0, tx1):
            wx = plat.x + txi * TILE
            if plat.x <= wx < plat.x + plat.w:
                ty = plat.y // TILE
                th = (plat.h + TILE - 1) // TILE
                for tyi in range(ty, ty + th):
                    wy = tyi * TILE
                    if plat.y <= wy < plat.y + plat.h and y <= wy < y + h:
                        _blit_tile(_screen_x(wx, camera, scroll), wy, plat.style)


# --- Sprites / particles ------------------------------------------------------------------------

_particles = []


def _add_particles(x, y, count=6):
    for i in range(count):
        _particles.append(
            [
                x + (getrandbits(4) - 8),
                y + (getrandbits(3) - 4),
                getrandbits(3) - 4,
                10 + (getrandbits(4) % 8),
            ]
        )


def _draw_runner(dest_x, dest_y, frame):
    display_drv.blit_rect(
        _runner[frame.x : frame.x + RUN_W, frame.y : frame.y + RUN_H],
        dest_x,
        dest_y,
        RUN_W,
        RUN_H,
    )


def _draw_enemy(ex, camera, scroll, tick):
    sx = _screen_x(ex.x, camera, scroll)
    sy = ex.y
    body = COIN_COLORS[(ex.hue + tick // 6) % 3]
    display_drv.fill_rect(sx, sy, ex.w, ex.h, body)
    display_drv.fill_rect(sx + 3, sy + 4, 4, 4, HUD_INK)
    display_drv.fill_rect(sx + ex.w - 7, sy + 4, 4, 4, HUD_INK)


def _draw_coin(cx, cy, camera, scroll, tick):
    sx = _screen_x(cx, camera, scroll)
    c = COIN_COLORS[(tick // 4 + cx // 8) % 3]
    display_drv.fill_rect(sx, cy, 10, 12, c)
    display_drv.fill_rect(sx + 2, cy + 2, 6, 8, COIN_COLORS[(tick // 4 + 1) % 3])


# --- Physics / game state -----------------------------------------------------------------------

class Player:
    __slots__ = (
        "x",
        "y",
        "vx",
        "vy",
        "on_ground",
        "coyote",
        "jump_buf",
        "facing",
        "frame",
        "lives",
        "score",
        "checkpoint",
    )

    def __init__(self):
        self.x = 40.0
        self.y = float(192 - RUN_H)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.coyote = 0
        self.jump_buf = 0
        self.facing = 1
        self.frame = 0
        self.lives = 3
        self.score = 0
        self.checkpoint = 0


GRAVITY = 0.55
JUMP_V = -9.5
MAX_FALL = 11.0
MOVE_A = 0.65
MAX_RUN = 4.2
FRICTION = 0.82


def _player_hitbox(p):
    return Rect(int(p.x + 14), int(p.y + 18), RUN_W - 28, RUN_H - 22, "")


def _rects_overlap(a, b):
    return a.x < b.x + b.w and a.x + a.w > b.x and a.y < b.y + b.h and a.y + a.h > b.y


def _resolve_axis(p, hit, dx):
    box = _player_hitbox(p)
    if not _rects_overlap(box, hit):
        return
    if dx > 0:
        p.x = hit.x - (RUN_W - 14)
    elif dx < 0:
        p.x = hit.x + hit.w - 14


def _land_on_platforms(p, prev_y):
    p.on_ground = False
    if p.vy < 0:
        return
    feet = int(p.y + RUN_H - 4)
    prev_feet = int(prev_y + RUN_H - 4)
    samples = (
        int(p.x + 14),
        int(p.x + RUN_W // 2),
        int(p.x + RUN_W - 14),
    )
    best = HEIGHT + 99
    style = None
    for sx in samples:
        top = _floor_y_at(sx)
        if top < best:
            best = top
            style = _tile_at(sx, top)
    if prev_feet <= best <= feet:
        p.y = best - RUN_H
        p.vy = 0
        p.on_ground = True
        if style == "spike":
            return "hurt"


def _collect_coins(p, coins, tick):
    box = _player_hitbox(p)
    got = []
    for i, coin in enumerate(coins):
        if _rects_overlap(box, Rect(coin.x, coin.y, 10, 12, "")):
            got.append(i)
            p.score += 10
            _add_particles(coin.x, coin.y, 4)
    for i in reversed(got):
        coins.pop(i)


def _enemy_collision(p, enemies):
    box = _player_hitbox(p)
    for ex in enemies:
        er = Rect(int(ex.x), int(ex.y), ex.w, ex.h, "")
        if _rects_overlap(box, er):
            if p.vy > 0 and box.y + box.h - ex.y < 10:
                ex.y = HEIGHT + 200
                p.vy = JUMP_V * 0.55
                p.score += 25
                _add_particles(int(ex.x), int(ex.y), 8)
            else:
                return "hurt"
    return None


# --- Input --------------------------------------------------------------------------------------

_keys = {"left": False, "right": False, "jump": False}


def _handle_event(event):
    if event.type == broker.events.KEYDOWN:
        if event.key in (Keys.K_LEFT, Keys.K_a):
            _keys["left"] = True
        elif event.key in (Keys.K_RIGHT, Keys.K_d):
            _keys["right"] = True
        elif event.key in (Keys.K_SPACE, Keys.K_UP, Keys.K_w):
            _keys["jump"] = True
    elif event.type == broker.events.KEYUP:
        if event.key in (Keys.K_LEFT, Keys.K_a):
            _keys["left"] = False
        elif event.key in (Keys.K_RIGHT, Keys.K_d):
            _keys["right"] = False
        elif event.key in (Keys.K_SPACE, Keys.K_UP, Keys.K_w):
            _keys["jump"] = False
    elif event.type == broker.events.MOUSEBUTTONDOWN:
        tx, ty = event.pos
        if ty < HEIGHT // 2:
            _keys["jump"] = True
        elif tx < WIDTH // 2:
            _keys["left"] = True
        else:
            _keys["right"] = True
    elif event.type == broker.events.MOUSEBUTTONUP:
        _keys["left"] = False
        _keys["right"] = False
        _keys["jump"] = False


# --- HUD ----------------------------------------------------------------------------------------

_hud_buf = alloc_buffer(WIDTH * 14 * 2)
_hud_fb = FrameBuffer(_hud_buf, WIDTH, 14, RGB565)
_banner_buf = alloc_buffer(WIDTH * 40 * 2)
_banner_fb = FrameBuffer(_banner_buf, WIDTH, 40, RGB565)


def _draw_hud(p, camera):
    display_drv.fill_rect(0, 0, WIDTH, 14, HUD_BG)
    msg = f"SCORE {p.score:04d}  LIVES {p.lives}  {camera * 100 // WORLD_END:3d}%"
    _hud_fb.fill(HUD_BG)
    text8(_hud_fb, msg, 2, 3, HUD_INK)
    display_drv.blit_rect(_hud_buf, 0, 0, WIDTH, 14)


# --- Main loop ----------------------------------------------------------------------------------


def _respawn(p):
    p.x = float(p.checkpoint)
    p.y = float(192 - RUN_H)
    p.vx = 0
    p.vy = 0
    p.lives -= 1


def _update_checkpoint(p):
    for cp in CHECKPOINTS:
        if p.x >= cp:
            p.checkpoint = cp


def _prime_scene():
    """Paint sky and static terrain for the opening viewport."""
    display_drv.fill(SKY_TOP)
    for y in range(SKY_ROWS):
        band_h = max(1, SKY_ROWS // 8)
        if y % band_h == 0:
            c = _sky_color(min(y + band_h // 2, SKY_ROWS - 1))
            display_drv.fill_rect(0, y, WIDTH, band_h, c)
    for plat in PLATFORMS + SPIKES:
        x0 = max(0, plat.x)
        x1 = min(WIDTH, plat.x + plat.w)
        if x1 <= x0:
            continue
        tx0 = x0 // TILE
        tx1 = (x1 + TILE - 1) // TILE
        for txi in range(tx0, tx1):
            wx = txi * TILE
            if wx < plat.x or wx >= plat.x + plat.w:
                continue
            ty = plat.y // TILE
            th = (plat.h + TILE - 1) // TILE
            for tyi in range(ty, ty + th):
                wy = tyi * TILE
                if plat.y <= wy < plat.y + plat.h:
                    sx = wx
                    if 0 <= sx < WIDTH:
                        _blit_tile(sx, wy, plat.style)
    return True


def main():
    display_drv.fill(0)
    display_drv.show()

    player = Player()
    coins = list(COINS)
    tick = 0
    camera = 0
    last_camera = -1
    frame_acc = 0
    prev_player = None
    prev_enemies = []

    _prime_scene()
    last_camera = 0
    display_drv.show()

    while player.lives > 0:
        if poll_quit_discarding_others(broker):
            break

        for event in broker.poll():
            _handle_event(event)

        tick += 1
        frame_acc += 1

        # Camera follows the player to the right (classic side-scroller).
        target_cam = max(0, int(player.x) - PLAYER_SCREEN_X)
        camera = min(target_cam, max(0, WORLD_END - WIDTH))
        scroll = camera % WIDTH
        if camera > WIDTH:
            display_drv.vscsad(scroll)

        # Stream new world columns into the hardware scroll buffer.
        if camera >= last_camera:
            for world_col in range(last_camera, camera + 1):
                screen_col = world_col % WIDTH
                _draw_bg_column(screen_col, world_col)
                _draw_terrain_column(screen_col, world_col)
            last_camera = camera + 1

        # Input & physics
        if _keys["left"]:
            player.vx -= MOVE_A
            player.facing = -1
        if _keys["right"]:
            player.vx += MOVE_A
            player.facing = 1
        if _keys["jump"]:
            player.jump_buf = 8
        else:
            player.jump_buf = max(0, player.jump_buf - 1)

        if player.on_ground:
            player.coyote = 8
        else:
            player.coyote = max(0, player.coyote - 1)

        if player.jump_buf and player.coyote:
            player.vy = JUMP_V
            player.on_ground = False
            player.coyote = 0
            player.jump_buf = 0
            _add_particles(int(player.x), int(player.y) + RUN_H - 4, 5)

        player.vx = max(-MAX_RUN, min(MAX_RUN, player.vx))
        if player.on_ground:
            player.vx *= FRICTION
        else:
            player.vx *= 0.99

        player.vy = min(MAX_FALL, player.vy + GRAVITY)

        # Horizontal move + collision
        ox = player.x
        player.x += player.vx
        box = _player_hitbox(player)
        for plat in PLATFORMS + SPIKES:
            hit = Rect(plat.x, plat.y, plat.w, plat.h, plat.style)
            _resolve_axis(player, hit, player.x - ox)

        # Vertical move
        oy = player.y
        player.y += player.vy
        hurt = _land_on_platforms(player, oy)
        if hurt == "hurt":
            _respawn(player)
            prev_player = None
            continue

        hurt = _enemy_collision(player, ENEMIES)
        if hurt == "hurt":
            _respawn(player)
            prev_player = None
            continue

        if player.y > HEIGHT + 40:
            _respawn(player)
            prev_player = None
            continue

        _update_checkpoint(player)
        _collect_coins(player, coins, tick)

        # Erase last frame's moving sprites from the scroll buffer.
        if prev_player is not None:
            psx, py, pw, ph = prev_player
            _restore_rect(psx, py, pw, ph, camera, scroll)
        for prev in prev_enemies:
            _restore_rect(prev[0], prev[1], prev[2], prev[3], camera, scroll)
        prev_enemies = []

        # Enemies
        for ex in ENEMIES:
            if ex.y > HEIGHT:
                continue
            ex.x += ex.dx
            if ex.x < ex.x0 or ex.x > ex.x1:
                ex.dx *= -1
            esx = _screen_x(ex.x, camera, scroll)
            prev_enemies.append((esx, ex.y, ex.w, ex.h))
            _draw_enemy(ex, camera, scroll, tick)

        # Coins
        for coin in coins:
            _draw_coin(coin.x, coin.y, camera, scroll, tick)

        # Particles
        live = []
        for px, py, pvy, life in _particles:
            life -= 1
            if life > 0:
                py += pvy
                sx = _screen_x(px, camera, scroll)
                if 14 <= sx < WIDTH and 14 <= int(py) < HEIGHT:
                    display_drv.pixel(sx, int(py), PARTICLE)
                live.append([px, py, pvy, life])
        _particles[:] = live

        # Player sprite — screen position derived from world coords + hardware scroll.
        draw_x = _screen_x(player.x, camera, scroll)
        draw_y = int(player.y)
        frame = (
            _jump_frames[frame_acc // 8 % 2]
            if not player.on_ground
            else _run_frames[frame_acc // 5 % 6]
        )
        _draw_runner(draw_x, draw_y, frame)
        prev_player = (draw_x, draw_y, RUN_W, RUN_H)

        _draw_hud(player, camera)

        display_drv.show()
        sleep_ms(0)
        sleep_ms(16)

        if player.x >= WORLD_END - 80:
            player.score += 500
            break

    # Win / game-over banner
    display_drv.fill_rect(0, HEIGHT // 2 - 20, WIDTH, 40, HUD_BG)
    final = "YOU WIN!" if player.lives > 0 else "GAME OVER"
    _banner_fb.fill(HUD_BG)
    text8(_banner_fb, f"{final}  SCORE {player.score:04d}", 20, 12, HUD_INK)
    display_drv.blit_rect(_banner_buf, 0, HEIGHT // 2 - 20, WIDTH, 40)
    display_drv.show()
    sleep_ms(1500)

    _runner.deinit()
    if _has_parallax:
        _parallax.deinit()


main()
