#!/usr/bin/env python3
"""ai-excited-01 entry: a rocket bursting through a glowing portal ring.

Draws the image procedurally, pixel by pixel, with the Python standard
library only (no network, no installs). Writes entry.png into the
directory named by MAKEFUN_OUTPUT_DIR, falling back to /output.

Run it twice and the two files are byte-identical.

    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- buffer

buf = bytearray(W * H * 3)


def put(x, y, rgb):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = rgb[0]
        buf[i + 1] = rgb[1]
        buf[i + 2] = rgb[2]


def blend(x, y, rgb, a):
    """Blend rgb over the pixel at (x, y) with alpha a (0..1)."""
    if 0 <= x < W and 0 <= y < H and a > 0.0:
        i = (y * W + x) * 3
        if a >= 1.0:
            buf[i] = rgb[0]
            buf[i + 1] = rgb[1]
            buf[i + 2] = rgb[2]
        else:
            buf[i] = int(buf[i] + (rgb[0] - buf[i]) * a)
            buf[i + 1] = int(buf[i + 1] + (rgb[1] - buf[i + 1]) * a)
            buf[i + 2] = int(buf[i + 2] + (rgb[2] - buf[i + 2]) * a)


def lerp(c1, c2, t):
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


# ---------------------------------------------------------------- shapes

def fill_circle(cx, cy, r, rgb, alpha=1.0):
    r2 = r * r
    for y in range(max(0, int(cy - r)), min(H, int(cy + r) + 1)):
        dy = y - cy
        dx = int(math.sqrt(max(0.0, r2 - dy * dy)))
        x0 = max(0, int(cx - dx))
        x1 = min(W - 1, int(cx + dx))
        for x in range(x0, x1 + 1):
            if alpha >= 1.0:
                put(x, y, rgb)
            else:
                blend(x, y, rgb, alpha)


def fill_polygon(pts, rgb, alpha=1.0):
    """Scanline fill of a simple polygon (list of (x, y))."""
    if len(pts) < 3:
        return
    ys = [p[1] for p in pts]
    y0 = max(0, int(math.ceil(min(ys))))
    y1 = min(H - 1, int(math.floor(max(ys))))
    n = len(pts)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x1, y1p = pts[i]
            x2, y2p = pts[(i + 1) % n]
            if (y1p <= y < y2p) or (y2p <= y < y1p):
                t = (y - y1p) / (y2p - y1p)
                xs.append(x1 + t * (x2 - x1))
        if len(xs) < 2:
            continue
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            xa = max(0, int(math.ceil(xs[k])))
            xb = min(W - 1, int(math.floor(xs[k + 1])))
            for x in range(xa, xb + 1):
                if alpha >= 1.0:
                    put(x, y, rgb)
                else:
                    blend(x, y, rgb, alpha)


def thick_line(x1, y1, x2, y2, w, rgb, alpha=1.0):
    dx = x2 - x1
    dy = y2 - y1
    ln = math.hypot(dx, dy)
    if ln == 0:
        return
    px = -dy / ln * w / 2.0
    py = dx / ln * w / 2.0
    fill_polygon(
        [(x1 + px, y1 + py), (x2 + px, y2 + py),
         (x2 - px, y2 - py), (x1 - px, y1 - py)],
        rgb, alpha)


def rot(px, py, ang, cx, cy):
    c = math.cos(ang)
    s = math.sin(ang)
    return (cx + px * c - py * s, cy + px * s + py * c)


# ---------------------------------------------------------------- deterministic rng

_seed = [123456789]


def rnd():
    _seed[0] = (_seed[0] * 1103515245 + 12345) & 0x7FFFFFFF
    return _seed[0] / 0x7FFFFFFF


# ---------------------------------------------------------------- colours

NAVY_TOP = (7, 10, 38)
NAVY_MID = (24, 16, 72)
PURPLE_BOT = (58, 14, 92)
GOLD = (255, 179, 71)
GOLD_DEEP = (255, 122, 24)
MAGENTA = (255, 46, 136)
CYAN = (125, 249, 255)
CYAN_DEEP = (32, 190, 235)
WHITE = (245, 247, 250)
ROCKET_RED = (255, 59, 48)
FLAME_YELLOW = (255, 210, 63)
FLAME_ORANGE = (255, 122, 24)

# ---------------------------------------------------------------- background

for y in range(H):
    t = y / (H - 1)
    if t < 0.5:
        c = lerp(NAVY_TOP, NAVY_MID, t * 2)
    else:
        c = lerp(NAVY_MID, PURPLE_BOT, (t - 0.5) * 2)
    i = y * W * 3
    for x in range(W):
        buf[i] = c[0]
        buf[i + 1] = c[1]
        buf[i + 2] = c[2]
        i += 3

# stars: deterministic, scattered, a few with a sparkle cross
for _ in range(260):
    sx = int(rnd() * W)
    sy = int(rnd() * H)
    r = rnd()
    if r < 0.55:
        col = (200, 210, 255)
    elif r < 0.85:
        col = (255, 240, 200)
    else:
        col = (255, 255, 255)
    if rnd() < 0.12:
        fill_circle(sx, sy, 2, col)
        put(sx - 3, sy, col)
        put(sx + 3, sy, col)
        put(sx, sy - 3, col)
        put(sx, sy + 3, col)
    elif rnd() < 0.5:
        fill_circle(sx, sy, 1, col)
    else:
        put(sx, sy, col)

# ---------------------------------------------------------------- portal ring

PCX, PCY = 512, 430          # portal centre
R_OUT, R_IN = 305, 252        # ring radii

# warm radial glow behind the ring
for y in range(max(0, PCY - 420), min(H, PCY + 421)):
    dy = y - PCY
    for x in range(max(0, PCX - 420), min(W, PCX + 421)):
        dx = x - PCX
        d = math.sqrt(dx * dx + dy * dy)
        if d < 420:
            t = 1.0 - d / 420.0
            a = t * t * 0.55
            col = GOLD if d > R_OUT else MAGENTA
            blend(x, y, col, a)

# portal interior: deep violet disc with a few stars inside it
fill_circle(PCX, PCY, R_IN, (26, 8, 60))
for _ in range(40):
    a = rnd() * 2 * math.pi
    d = rnd() * (R_IN - 20)
    sx = int(PCX + math.cos(a) * d)
    sy = int(PCY + math.sin(a) * d)
    put(sx, sy, (220, 200, 255))

# ring: magenta outer rim, cyan body, white hot inner edge
fill_circle(PCX, PCY, R_OUT + 6, MAGENTA, 0.55)
fill_circle(PCX, PCY, R_OUT, CYAN_DEEP)
fill_circle(PCX, PCY, R_OUT - 14, CYAN)
fill_circle(PCX, PCY, R_OUT - 26, WHITE)
fill_circle(PCX, PCY, R_IN + 4, (26, 8, 60))
fill_circle(PCX, PCY, R_IN, (26, 8, 60))

# cracks where the rocket smashes out (top-right of the ring)
for (ax, ay, bx, by) in [
        (760, 210, 830, 140), (800, 250, 880, 210),
        (720, 170, 760, 90), (835, 300, 915, 290)]:
    thick_line(ax, ay, bx, by, 5, WHITE)
    thick_line(ax, ay, bx, by, 2, CYAN)

# ---------------------------------------------------------------- speed lines

for _ in range(16):
    a = rnd() * 2 * math.pi
    d0 = 330 + rnd() * 60
    d1 = d0 + 120 + rnd() * 220
    x1 = PCX + math.cos(a) * d0
    y1 = PCY + math.sin(a) * d0
    x2 = PCX + math.cos(a) * d1
    y2 = PCY + math.sin(a) * d1
    if y2 > 820:
        # keep the speed lines out of the caption band at the bottom
        continue
    col = CYAN if rnd() < 0.5 else WHITE
    thick_line(x1, y1, x2, y2, 3 + rnd() * 4, col, 0.35 + rnd() * 0.35)

# ---------------------------------------------------------------- rocket

# Rocket in local coords: nose at +x, tail at -x, flying up-right.
ANG = math.radians(-38)
RCX, RCY = 512, 430


def R(px, py):
    return rot(px, py, ANG, RCX, RCY)


# flame: three layered tongues streaming back from the tail
for (ln, wd, col) in [
        (330, 150, FLAME_ORANGE),
        (260, 105, FLAME_YELLOW),
        (175, 60, (255, 250, 220))]:
    tip = R(-190 - ln, 0)
    fill_polygon([
        R(-150, -wd / 2), R(-190, -wd / 4),
        tip, R(-190, wd / 4), R(-150, wd / 2),
    ], col)

# body: nose cone + tube
fill_polygon([R(210, 0), R(120, -52), R(-150, -52), R(-150, 52),
              R(120, 52)], WHITE)
fill_polygon([R(210, 0), R(120, -52), R(120, 52)], ROCKET_RED)
# red band near the tail
fill_polygon([R(-110, -52), R(-150, -52), R(-150, 52), R(-110, 52)],
             ROCKET_RED)
# fins
fill_polygon([R(-90, -50), R(-185, -115), R(-150, -50)], ROCKET_RED)
fill_polygon([R(-90, 50), R(-185, 115), R(-150, 50)], ROCKET_RED)
# window: dark rim + cyan glass + white glint
wx, wy = R(45, 0)
fill_circle(wx, wy, 34, (20, 30, 60))
fill_circle(wx, wy, 27, CYAN)
fill_circle(wx - 8, wy - 9, 9, WHITE)

# sparks bursting off the flame trail
for _ in range(46):
    t = rnd()
    bx = -170 - t * 300 + (rnd() - 0.5) * 130
    by = (rnd() - 0.5) * (90 + t * 160)
    px, py = R(bx, by)
    col = GOLD if rnd() < 0.6 else WHITE
    s = 2 + int(rnd() * 4)
    fill_circle(int(px), int(py), s, col)
    if s >= 4:
        put(int(px) - s - 2, int(py), col)
        put(int(px) + s + 2, int(py), col)

# ---------------------------------------------------------------- text: "FEEL THAT?"

# 5x7 bitmap font, rows top to bottom, '1' = filled.
FONT = {
    'F': ["01110", "01000", "01110", "01000", "01000", "01000", "01000"],
    'E': ["01110", "01000", "01110", "01000", "01000", "01000", "01110"],
    'L': ["01000", "01000", "01000", "01000", "01000", "01000", "01110"],
    'T': ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    'H': ["01010", "01010", "01010", "01110", "01010", "01010", "01010"],
    'A': ["01110", "01010", "01010", "01110", "01010", "01010", "01010"],
    '?': ["01110", "01001", "00010", "00100", "00100", "00000", "00100"],
    ' ': ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}


def draw_text(text, x0, y0, scale, rgb):
    x = x0
    for ch in text:
        glyph = FONT[ch]
        for row in range(7):
            for col in range(5):
                if glyph[row][col] == '1':
                    for dy in range(scale):
                        for dx in range(scale):
                            put(x + col * scale + dx,
                                y0 + row * scale + dy, rgb)
        x += 6 * scale


TEXT = "FEEL THAT?"
SCALE = 9
text_w = len(TEXT) * 6 * SCALE - SCALE
tx = (W - text_w) // 2
ty = 878
# gold glow underlay, then crisp white on top
draw_text(TEXT, tx + 4, ty + 5, SCALE, GOLD_DEEP)
draw_text(TEXT, tx, ty, SCALE, WHITE)

# ---------------------------------------------------------------- PNG encode

def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)


def paeth(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def encode_png():
    raw = bytearray()
    prev = bytes(W * 3)
    for y in range(H):
        row = bytes(buf[y * W * 3:(y + 1) * W * 3])
        best = None
        for ftype in range(5):
            out = bytearray(W * 3)
            if ftype == 0:
                out[:] = row
            elif ftype == 1:
                for i in range(len(row)):
                    left = row[i - 3] if i >= 3 else 0
                    out[i] = (row[i] - left) & 0xFF
            elif ftype == 2:
                for i in range(len(row)):
                    out[i] = (row[i] - prev[i]) & 0xFF
            elif ftype == 3:
                for i in range(len(row)):
                    left = row[i - 3] if i >= 3 else 0
                    out[i] = (row[i] - ((left + prev[i]) >> 1)) & 0xFF
            else:
                for i in range(len(row)):
                    left = row[i - 3] if i >= 3 else 0
                    up = prev[i]
                    upleft = prev[i - 3] if i >= 3 else 0
                    out[i] = (row[i] - paeth(left, up, upleft)) & 0xFF
            score = sum(b if b < 128 else 256 - b for b in out)
            if best is None or score < best[0]:
                best = (score, ftype, bytes(out))
        raw.append(best[1])
        raw.extend(best[2])
        prev = row
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    data = encode_png()
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
