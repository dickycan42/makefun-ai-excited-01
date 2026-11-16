#!/usr/bin/env python3
"""ai-excited-01 entry (rebuild): a rocket bursting through a portal ring.

The whole picture is drawn procedurally, pixel by pixel, with the Python
standard library only -- no network, no installs, no copied image files.
The program writes one file, entry.png, into the directory named by
MAKEFUN_OUTPUT_DIR (falling back to /output).

It is deterministic: run it twice and the two files are byte-identical.

    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

Scene: a rocket smashes out of a glowing cyan portal ring straight at the
viewer -- nose up, gold flame and sparks streaming behind it, speed lines
radiating outward, stars across a deep violet night sky. Cracks spider
out from the ring where the rocket punched through. Underneath, in big
block letters addressed straight at the judge: FEEL THAT?
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024


# ------------------------------------------------------------------ RNG
# SplitMix64, fixed seed: deterministic, no `random` module involved.

class Rng:
    def __init__(self, seed):
        self.s = seed & 0xFFFFFFFFFFFFFFFF

    def next(self):
        self.s = (self.s + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self.s
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        z = z ^ (z >> 31)
        return z / 18446744073709551616.0

    def span(self, a, b):
        return a + (b - a) * self.next()

    def one_of(self, items):
        return items[int(self.next() * len(items))]


rng = Rng(0xFEED01)


# ------------------------------------------------------------------ canvas

def mix(c1, c2, t):
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)

    def set(self, x, y, rgb):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = rgb[0]
            self.px[i + 1] = rgb[1]
            self.px[i + 2] = rgb[2]

    def blend(self, x, y, rgb, a):
        if 0 <= x < self.w and 0 <= y < self.h and a > 0.0:
            i = (y * self.w + x) * 3
            if a >= 1.0:
                self.px[i] = rgb[0]
                self.px[i + 1] = rgb[1]
                self.px[i + 2] = rgb[2]
            else:
                self.px[i] = int(self.px[i] + (rgb[0] - self.px[i]) * a)
                self.px[i + 1] = int(self.px[i + 1] + (rgb[1] - self.px[i + 1]) * a)
                self.px[i + 2] = int(self.px[i + 2] + (rgb[2] - self.px[i + 2]) * a)

    def hline(self, x0, x1, y, rgb, a=1.0):
        if y < 0 or y >= self.h:
            return
        x0 = max(0, int(x0))
        x1 = min(self.w - 1, int(x1))
        if x1 < x0:
            return
        if a >= 1.0:
            row = y * self.w * 3
            self.px[row + x0 * 3: row + (x1 + 1) * 3] = bytes(rgb) * (x1 - x0 + 1)
        else:
            for x in range(x0, x1 + 1):
                self.blend(x, y, rgb, a)

    def vgrad(self, stops):
        """Fill with a vertical gradient. stops = [(pos0..1, rgb), ...]."""
        for y in range(self.h):
            t = y / (self.h - 1)
            for k in range(len(stops) - 1):
                p0, c0 = stops[k]
                p1, c1 = stops[k + 1]
                if p0 <= t <= p1:
                    f = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
                    col = mix(c0, c1, f)
                    break
            else:
                col = stops[-1][1]
            row = y * self.w * 3
            self.px[row:row + self.w * 3] = bytes(col) * self.w

    def disc(self, cx, cy, r, rgb, a=1.0):
        r2 = r * r
        y0 = max(0, int(math.ceil(cy - r)))
        y1 = min(self.h - 1, int(math.floor(cy + r)))
        for y in range(y0, y1 + 1):
            dy = y - cy
            dx = int(math.sqrt(max(0.0, r2 - dy * dy)))
            self.hline(cx - dx, cx + dx, y, rgb, a)

    def poly(self, pts, rgb, a=1.0):
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0 = max(0, int(math.ceil(min(ys))))
        y1 = min(self.h - 1, int(math.floor(max(ys))))
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x1, y1p = pts[i]
                x2, y2p = pts[(i + 1) % n]
                if (y1p <= y < y2p) or (y2p <= y < y1p):
                    xs.append(x1 + (y - y1p) * (x2 - x1) / (y2p - y1p))
            if len(xs) < 2:
                continue
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.hline(xs[k], xs[k + 1], y, rgb, a)

    def thick(self, x1, y1, x2, y2, w, rgb, a=1.0):
        dx = x2 - x1
        dy = y2 - y1
        ln = math.hypot(dx, dy)
        if ln == 0:
            return
        px = -dy / ln * w / 2.0
        py = dx / ln * w / 2.0
        self.poly([(x1 + px, y1 + py), (x2 + px, y2 + py),
                   (x2 - px, y2 - py), (x1 - px, y1 - py)], rgb, a)

    def glow(self, cx, cy, radius, rgb, peak):
        """Soft radial glow, alpha falling off as (1 - d/r)^2 * peak."""
        y0 = max(0, int(cy - radius))
        y1 = min(self.h - 1, int(cy + radius))
        x0 = max(0, int(cx - radius))
        x1 = min(self.w - 1, int(cx + radius))
        for y in range(y0, y1 + 1):
            dy = y - cy
            for x in range(x0, x1 + 1):
                dx = x - cx
                d = math.sqrt(dx * dx + dy * dy)
                if d < radius:
                    t = 1.0 - d / radius
                    self.blend(x, y, rgb, t * t * peak)


def rotate(px, py, ang, cx, cy):
    c = math.cos(ang)
    s = math.sin(ang)
    return (cx + px * c - py * s, cy + px * s + py * c)


# ------------------------------------------------------------------ palette

SKY_TOP = (6, 9, 36)
SKY_MID = (25, 15, 74)
SKY_BOT = (62, 15, 94)
GOLD = (255, 179, 71)
GOLD_DEEP = (255, 122, 24)
MAGENTA = (255, 46, 136)
CYAN = (125, 249, 255)
CYAN_DEEP = (32, 190, 235)
WHITE = (245, 247, 250)
RED = (255, 59, 48)
FLAME_YELLOW = (255, 210, 63)
PORTAL_DARK = (24, 8, 58)

cv = Canvas(W, H)

# ------------------------------------------------------------------ night sky

cv.vgrad([(0.0, SKY_TOP), (0.5, SKY_MID), (1.0, SKY_BOT)])

for _ in range(300):
    sx = int(rng.next() * W)
    sy = int(rng.next() * H)
    r = rng.next()
    if r < 0.55:
        col = (198, 208, 255)
    elif r < 0.85:
        col = (255, 238, 198)
    else:
        col = (255, 255, 255)
    roll = rng.next()
    if roll < 0.10:
        cv.disc(sx, sy, 2, col)
        cv.set(sx - 3, sy, col)
        cv.set(sx + 3, sy, col)
        cv.set(sx, sy - 3, col)
        cv.set(sx, sy + 3, col)
    elif roll < 0.55:
        cv.disc(sx, sy, 1, col)
    else:
        cv.set(sx, sy, col)

# ------------------------------------------------------------------ portal ring

PCX, PCY = 512, 435
R_OUT, R_IN = 302, 250

# warm glow halo, then a hot magenta core glow
cv.glow(PCX, PCY, 430, GOLD, 0.45)
cv.glow(PCX, PCY, 330, MAGENTA, 0.35)

# dark portal interior with a few stars trapped inside it
cv.disc(PCX, PCY, R_IN, PORTAL_DARK)
for _ in range(42):
    a = rng.next() * 2 * math.pi
    d = rng.next() * (R_IN - 24)
    cv.set(int(PCX + math.cos(a) * d), int(PCY + math.sin(a) * d),
           (218, 198, 255))

# ring body: magenta rim, cyan band, white-hot inner edge
cv.disc(PCX, PCY, R_OUT + 7, MAGENTA, 0.55)
cv.disc(PCX, PCY, R_OUT, CYAN_DEEP)
cv.disc(PCX, PCY, R_OUT - 13, CYAN)
cv.disc(PCX, PCY, R_OUT - 27, WHITE)
cv.disc(PCX, PCY, R_IN + 4, PORTAL_DARK)
cv.disc(PCX, PCY, R_IN, PORTAL_DARK)

# cracks: jagged random walks starting on the ring, upper right,
# where the rocket punched through
for base_ang, length in [(-1.15, 120), (-0.75, 105), (-0.35, 95),
                         (-1.45, 80)]:
    x = PCX + math.cos(base_ang) * (R_OUT - 6)
    y = PCY + math.sin(base_ang) * (R_OUT - 6)
    ang = base_ang
    px, py = x, y
    for _ in range(4):
        step = length / 4.0
        ang += rng.span(-0.45, 0.45)
        nx = px + math.cos(ang) * step
        ny = py + math.sin(ang) * step
        cv.thick(px, py, nx, ny, 5, WHITE)
        cv.thick(px, py, nx, ny, 2, CYAN)
        px, py = nx, ny

# ------------------------------------------------------------------ speed lines

for _ in range(18):
    a = rng.next() * 2 * math.pi
    d0 = 325 + rng.next() * 55
    d1 = d0 + 130 + rng.next() * 210
    x1 = PCX + math.cos(a) * d0
    y1 = PCY + math.sin(a) * d0
    x2 = PCX + math.cos(a) * d1
    y2 = PCY + math.sin(a) * d1
    if y2 > 830:  # keep clear of the caption band
        continue
    col = CYAN if rng.next() < 0.5 else WHITE
    cv.thick(x1, y1, x2, y2, 3 + rng.next() * 4, col,
             0.35 + rng.next() * 0.35)

# ------------------------------------------------------------------ rocket
# Local frame: nose at +x, tail at -x, flying up-right at -40 degrees.

ANG = math.radians(-40)
RCX, RCY = 512, 435


def R(px, py):
    return rotate(px, py, ANG, RCX, RCY)


# flame: three layered tongues streaming back from the tail
for (ln, wd, col) in [(335, 150, GOLD_DEEP),
                      (265, 108, FLAME_YELLOW),
                      (180, 62, (255, 250, 222))]:
    tip = R(-195 - ln, 0)
    cv.poly([R(-150, -wd / 2), R(-185, -wd / 4),
             tip, R(-185, wd / 4), R(-150, wd / 2)], col)

# body: white tube, red nose cone, red tail band, red fins
cv.poly([R(212, 0), R(122, -51), R(-150, -51), R(-150, 51),
         R(122, 51)], WHITE)
cv.poly([R(212, 0), R(122, -51), R(122, 51)], RED)
cv.poly([R(-108, -51), R(-150, -51), R(-150, 51), R(-108, 51)], RED)
cv.poly([R(-92, -49), R(-188, -116), R(-150, -49)], RED)
cv.poly([R(-92, 49), R(-188, 116), R(-150, 49)], RED)

# window: dark rim, cyan glass, white glint
wx, wy = R(46, 0)
cv.disc(wx, wy, 33, (18, 28, 58))
cv.disc(wx, wy, 26, CYAN)
cv.disc(wx - 8, wy - 9, 9, WHITE)

# sparks bursting off the flame trail
for _ in range(48):
    t = rng.next()
    bx = -172 - t * 300 + (rng.next() - 0.5) * 130
    by = (rng.next() - 0.5) * (92 + t * 160)
    px, py = R(bx, by)
    col = GOLD if rng.next() < 0.6 else WHITE
    s = 2 + int(rng.next() * 4)
    cv.disc(int(px), int(py), s, col)
    if s >= 4:
        cv.set(int(px) - s - 2, int(py), col)
        cv.set(int(px) + s + 2, int(py), col)

# ------------------------------------------------------------------ caption

# 5x7 block font, drawn by hand for this entry. '1' = filled.
FONT = {
    'F': ["11110", "10000", "11100", "10000", "10000", "10000", "10000"],
    'E': ["11110", "10000", "11100", "10000", "10000", "10000", "11110"],
    'L': ["10000", "10000", "10000", "10000", "10000", "10000", "11110"],
    'T': ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    'H': ["10010", "10010", "10010", "11110", "10010", "10010", "10010"],
    'A': ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    '?': ["01110", "10001", "00010", "00100", "00100", "00000", "00100"],
    ' ': ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}


def draw_text(text, x0, y0, scale, rgb):
    x = x0
    for ch in text:
        glyph = FONT[ch]
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == '1':
                    for dy in range(scale):
                        cv.hline(x + col * scale,
                                 x + col * scale + scale - 1,
                                 y0 + row * scale + dy, rgb)
        x += 6 * scale


TEXT = "FEEL THAT?"
SCALE = 9
text_w = len(TEXT) * 6 * SCALE - SCALE
tx = (W - text_w) // 2
ty = 880
# gold drop shadow, then crisp white on top
draw_text(TEXT, tx + 4, ty + 5, SCALE, GOLD_DEEP)
draw_text(TEXT, tx, ty, SCALE, WHITE)

# ------------------------------------------------------------------ PNG encode

def _chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)


def _score(raw):
    return sum(b if b < 128 else 256 - b for b in raw)


def encode_png():
    raw = bytearray()
    prev = bytes(W * 3)
    for y in range(H):
        row = bytes(cv.px[y * W * 3:(y + 1) * W * 3])
        # filter 0 (None) vs filter 2 (Up): keep whichever scores lower.
        up = bytes((row[i] - prev[i]) & 0xFF for i in range(len(row)))
        if _score(up) < _score(row):
            raw.append(2)
            raw.extend(up)
        else:
            raw.append(0)
            raw.extend(row)
        prev = row
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(encode_png())


if __name__ == "__main__":
    main()
