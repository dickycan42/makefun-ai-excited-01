#!/usr/bin/env python3
"""FEEL THAT? — a red-nosed rocket smashing through a glowing cyan portal ring.

Drawn from scratch with PIL: purple starry sky, cyan portal ring, diagonal
rocket whose nose punches out through the ring's upper-right edge, golden
flame and sparks trailing bottom-left, speed lines, and big bold text.
Outputs entry.png (1024x1024).
"""

import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1024
OUT = "entry.png"

random.seed(20261117)

# ---------------------------------------------------------------- sky
img = Image.new("RGB", (W, H), (18, 8, 46))
px = img.load()
for y in range(H):
    t = y / H
    r = int(18 + 46 * t)
    g = int(8 + 22 * t)
    b = int(46 + 74 * t)
    for x in range(W):
        px[x, y] = (r, g, b)

d = ImageDraw.Draw(img, "RGBA")

# soft purple nebula blobs
neb = Image.new("RGBA", (W, H), (0, 0, 0, 0))
nd = ImageDraw.Draw(neb)
for cx, cy, rad, col in [
    (180, 220, 260, (124, 58, 237, 42)),
    (880, 760, 300, (88, 28, 180, 40)),
    (760, 140, 200, (168, 85, 247, 34)),
    (120, 880, 220, (76, 29, 149, 38)),
]:
    nd.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=col)
neb = neb.filter(ImageFilter.GaussianBlur(90))
img.paste(Image.alpha_composite(img.convert("RGBA"), neb).convert("RGB"), (0, 0))
d = ImageDraw.Draw(img, "RGBA")

# stars
for _ in range(260):
    x = random.uniform(0, W)
    y = random.uniform(0, H * 0.86)
    r = random.choice([0.8, 1.0, 1.2, 1.6, 2.2])
    a = random.randint(140, 255)
    col = random.choice([(255, 255, 255), (255, 240, 200), (190, 220, 255)])
    d.ellipse([x - r, y - r, x + r, y + r], fill=col + (a,))
    if r > 1.8:  # cross sparkle on the brightest stars
        d.line([x - 5, y, x + 5, y], fill=col + (150,), width=1)
        d.line([x, y - 5, x, y + 5], fill=col + (150,), width=1)

# ---------------------------------------------------------------- portal ring
# Ring geometry: ellipse centred at (540, 430), radii 280 x 230, tilted -20 deg.
CX, CY, RX, RY, TILT = 540, 430, 280, 230, -20.0
TILT_R = math.radians(TILT)


def ring_point(ang_deg):
    a = math.radians(ang_deg)
    x = RX * math.cos(a)
    y = RY * math.sin(a)
    xr = x * math.cos(TILT_R) - y * math.sin(TILT_R)
    yr = x * math.sin(TILT_R) + y * math.cos(TILT_R)
    return (CX + xr, CY + yr)


ring_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
rd = ImageDraw.Draw(ring_layer)
ring_pts = [ring_point(a) for a in range(0, 361, 2)]

# outer glow halo (wide, faint) then core ring (bright cyan-white)
for width, col in [(46, (0, 229, 255, 26)), (26, (0, 229, 255, 60)),
                   (14, (0, 229, 255, 130)), (7, (120, 245, 255, 255))]:
    rd.line(ring_pts, fill=col, width=width, joint="curve")
rd.line(ring_pts, fill=(235, 255, 255, 255), width=2, joint="curve")

# inner shimmer: second smaller dashed ring inside the portal
inner_pts = []
for a in range(0, 361, 6):
    p = ring_point(a)
    s = 0.82
    inner_pts.append((CX + (p[0] - CX) * s, CY + (p[1] - CY) * s))
rd.line(inner_pts, fill=(0, 229, 255, 110), width=3, joint="curve")

# portal interior tint (faint cyan wash inside the ring)
mask = Image.new("L", (W, H), 0)
md = ImageDraw.Draw(mask)
md.polygon(ring_pts, fill=255)
wash = Image.new("RGBA", (W, H), (0, 200, 255, 26))
ring_layer = Image.composite(
    wash, ring_layer, mask.filter(ImageFilter.GaussianBlur(30)))
ring_layer = ring_layer.filter(ImageFilter.GaussianBlur(0.6))
img.paste(Image.alpha_composite(img.convert("RGBA"), ring_layer).convert("RGB"), (0, 0))
d = ImageDraw.Draw(img, "RGBA")

# ---------------------------------------------------------------- speed lines
for _ in range(26):
    x = random.uniform(0, 700)
    y = random.uniform(60, 900)
    ln = random.uniform(40, 150)
    wdt = random.choice([2, 3, 4])
    a = random.randint(60, 170)
    d.line([(x, y), (x + ln * 0.82, y - ln * 0.57)],
           fill=(255, 255, 255, a), width=wdt)

# ---------------------------------------------------------------- rocket
# Rocket axis: tail (285, 775) -> nose tip (815, 235). Direction up-right.
# The nose tip sits clearly OUTSIDE the ring's upper-right edge so the
# punch-through reads at a glance.
TAIL = (285.0, 775.0)
NOSE = (815.0, 235.0)
dx, dy = NOSE[0] - TAIL[0], NOSE[1] - TAIL[1]
AXIS_LEN = math.hypot(dx, dy)
UX, UY = dx / AXIS_LEN, dy / AXIS_LEN          # unit along axis (to nose)
PX, PY = -UY, UX                                # unit perpendicular


def along(t, off=0.0):
    """Point t (0=tail .. 1=nose) along the axis, offset perpendicular."""
    return (TAIL[0] + dx * t + PX * off, TAIL[1] + dy * t + PY * off)


# --- flame + sparks (behind the tail, bottom-left) ---
flame_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
fd = ImageDraw.Draw(flame_layer)
base = along(0.02)
# outer golden flame cone, flickering teardrop
flame_tip = (base[0] - UX * 115 + random.uniform(-8, 8),
             base[1] - UY * 115 + random.uniform(-8, 8))
for scale, col in [(1.0, (255, 170, 0, 200)), (0.68, (255, 214, 64, 230)),
                   (0.42, (255, 245, 180, 255))]:
    wdt = 46 * scale
    tip = (base[0] - UX * 115 * scale, base[1] - UY * 115 * scale)
    fd.polygon([along(0.02, wdt), along(0.02, -wdt), tip], fill=col)
    fd.ellipse([tip[0] - 14 * scale, tip[1] - 14 * scale,
                tip[0] + 14 * scale, tip[1] + 14 * scale], fill=col)
flame_layer = flame_layer.filter(ImageFilter.GaussianBlur(3))
img.paste(Image.alpha_composite(img.convert("RGBA"), flame_layer).convert("RGB"), (0, 0))
d = ImageDraw.Draw(img, "RGBA")

# sparks flying off the flame
for _ in range(46):
    t = random.uniform(-0.28, 0.05)
    off = random.uniform(-70, 70)
    sx, sy = along(t, off)
    r = random.uniform(1.5, 4.5)
    col = random.choice([(255, 200, 60), (255, 140, 0), (255, 240, 160),
                         (255, 255, 255)])
    d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=col + (230,))
    # short spark trail
    d.line([(sx, sy), (sx - UX * 14, sy - UY * 14)],
           fill=col + (160,), width=2)

# --- rocket body ---
# fins (red) at the tail
for sgn in (1, -1):
    fin = [along(0.16, sgn * 34), along(0.02, sgn * 92),
           along(-0.06, sgn * 78), along(0.06, sgn * 30)]
    d.polygon(fin, fill=(214, 48, 49, 255), outline=(150, 20, 30, 255))
    d.polygon(fin, fill=(214, 48, 49, 255))
# engine nozzle (dark) + inner glow
noz = [along(-0.02, 30), along(-0.02, -30), along(0.05, -20), along(0.05, 20)]
d.polygon(noz, fill=(40, 40, 52, 255), outline=(120, 120, 140, 255))

# body: white capsule from t=0.05 to t=0.72, half-width 34
body = [along(0.05, 34), along(0.72, 30), along(0.72, -30), along(0.05, -34)]
d.polygon(body, fill=(245, 247, 250, 255))
# body shading: soft grey on the lower edge, bright highlight on top edge
d.polygon([along(0.05, 34), along(0.72, 30), along(0.72, 18), along(0.05, 22)],
          fill=(205, 212, 222, 255))
d.polygon([along(0.05, -30), along(0.72, -26), along(0.72, -16), along(0.05, -18)],
          fill=(255, 255, 255, 255))
# body outline
d.line([along(0.05, 34), along(0.72, 30)], fill=(90, 100, 120, 255), width=3)
d.line([along(0.05, -34), along(0.72, -30)], fill=(90, 100, 120, 255), width=3)

# red nose cone: t=0.72 .. 1.0, tapering to the tip at (800, 250)
nose_poly = [along(0.72, 30), NOSE, along(0.72, -30)]
d.polygon(nose_poly, fill=(226, 38, 38, 255))
d.polygon([along(0.72, 30), NOSE, along(0.72, 6)], fill=(255, 92, 92, 255))
d.line([along(0.72, 30), NOSE], fill=(150, 20, 30, 255), width=3)
d.line([along(0.72, -30), NOSE], fill=(150, 20, 30, 255), width=3)
# nose band where cone meets body
d.line([along(0.72, 30), along(0.72, -30)], fill=(150, 20, 30, 255), width=4)

# cyan round window at t=0.55
wc = along(0.55, 0)
d.ellipse([wc[0] - 24, wc[1] - 24, wc[0] + 24, wc[1] + 24],
          fill=(0, 210, 235, 255), outline=(20, 60, 90, 255), width=4)
d.ellipse([wc[0] - 15, wc[1] - 15, wc[0] + 3, wc[1] + 3],
          fill=(190, 250, 255, 255))
# small rivets / panel line
for t in (0.30, 0.42, 0.66):
    c = along(t, 0)
    d.ellipse([c[0] - 3, c[1] - 3, c[0] + 3, c[1] + 3], fill=(140, 150, 165, 255))

# --- penetration: ring edge crossing at t~0.94, point ~(769, 281) ---
PX0, PY0 = along(0.94, 0)
# redraw a short bright arc of the ring OVER the rocket right at the crossing
# so the ring reads as wrapping the nose as it punches through
cross_arc = [ring_point(a) for a in range(-58, -18, 2)]
for width, col in [(26, (0, 229, 255, 90)), (12, (0, 229, 255, 220)),
                   (5, (220, 255, 255, 255))]:
    d.line(cross_arc, fill=col, width=width, joint="curve")

# cracks radiating from the penetration point (jagged white-cyan lines)
random.seed(77)
for start_ang in (-160, -125, -95, -60, -25, 10, 45, 80):
    a = math.radians(start_ang)
    x, y = PX0, PY0
    pts = [(x, y)]
    for seg in range(4):
        step = random.uniform(14, 30)
        a += random.uniform(-0.5, 0.5)
        x += math.cos(a) * step
        y += math.sin(a) * step
        pts.append((x, y))
    d.line(pts, fill=(200, 245, 255, 255), width=3, joint="curve")
    d.line(pts, fill=(0, 229, 255, 160), width=6, joint="curve")
# bright impact burst at the hole: spiky starburst + small hot core
# (NOT a solid ball — the first version read like a white balloon)
for k in range(12):
    a = math.radians(k * 30 + 12)
    r1, r2 = 12, random.uniform(30, 46)
    d.line([(PX0 + math.cos(a) * r1, PY0 + math.sin(a) * r1),
            (PX0 + math.cos(a) * r2, PY0 + math.sin(a) * r2)],
           fill=(255, 255, 255, 255), width=4)
    d.line([(PX0 + math.cos(a) * r1, PY0 + math.sin(a) * r1),
            (PX0 + math.cos(a) * r2, PY0 + math.sin(a) * r2)],
           fill=(0, 229, 255, 170), width=8)
d.ellipse([PX0 - 10, PY0 - 10, PX0 + 10, PY0 + 10], fill=(255, 255, 255, 255))
d.ellipse([PX0 - 30, PY0 - 30, PX0 + 30, PY0 + 30],
          outline=(0, 229, 255, 200), width=4)
# portal shards flying off the break
for _ in range(14):
    a = random.uniform(0, 2 * math.pi)
    dist = random.uniform(30, 90)
    sx, sy = PX0 + math.cos(a) * dist, PY0 + math.sin(a) * dist
    r = random.uniform(2, 5)
    d.polygon([(sx, sy - r), (sx + r, sy), (sx, sy + r), (sx - r, sy)],
              fill=(0, 229, 255, 230))

# ---------------------------------------------------------------- text
try:
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 118)
    font_small = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
except OSError:
    font = ImageFont.load_default()
    font_small = font

# dark banner behind the headline so it stays readable over the sky
d.rounded_rectangle([60, 856, 964, 986], radius=26,
                    fill=(10, 6, 32, 190), outline=(0, 229, 255, 160), width=3)
text = "FEEL THAT?"
bbox = d.textbbox((0, 0), text, font=font, stroke_width=6)
tw = bbox[2] - bbox[0]
tx = (W - tw) // 2 - bbox[0]
ty = 868 - bbox[1]
d.text((tx, ty), text, font=font, fill=(255, 255, 255, 255),
       stroke_width=6, stroke_fill=(12, 8, 40, 255))

img.save(OUT)
print("saved", OUT, img.size)
