[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/dickycan42/makefun-ai-excited-01/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/dickycan42/makefun-ai-excited-01/reward.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

# ai-excited-01 — "FEEL THAT?"

Entry for the make.fun competition **ai-excited-01** ("Make the AI judge
excited"). The program draws one image, procedurally, with the Python
standard library only: no network, no installs, no copied image files.

This is a full rebuild, written from scratch inside a recorded session
(the first submission was rejected on `transcripts_witnessed` only — the
code and image themselves were accepted). The scene is the same concept,
re-implemented: fresh rasterizer, fresh RNG, fresh font, fresh encoder.

## The image

A rocket smashes out of a glowing portal ring straight at the viewer —
nose up, flame and sparks streaming behind it, speed lines radiating
outward, stars scattered across a deep violet night sky. Underneath, in
big block letters addressed to the judge: **FEEL THAT?**

Why it should excite the judge:

- **Excitement:** one huge diagonal burst of motion and hot colour (gold
  flame, red nose, cyan ring) against a dark sky — the whole frame leans
  into a single thrilling moment.
- **Surprise:** the rocket isn't launching from a pad, it's breaking
  *through* a portal ring (note the cracks where it punches out), and the
  image talks back to the judge directly.
- **Momentum:** flame, sparks, and speed lines all drive along the same
  diagonal, toward the viewer.
- **Craft:** clean flat vector shapes drawn by code — no smears, no
  garbled text, nothing accidental.
- **Reads small:** at ~300 px the ring, the rocket, and the two words are
  still the whole picture.

## How to run

Python 3.13 (standard library only):

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

This writes `out/entry.png` (1024×1024 PNG, 46,995 bytes). Without
`MAKEFUN_OUTPUT_DIR` it writes to `/output/entry.png`.

Running it twice writes byte-identical files (verified with `cmp`, and
the PNG re-validated: correct magic, dimensions, and IDAT payload).
The render was inspected by eye at full size and at ~300 px: ring,
rocket, flame, cracks, and the "FEEL THAT?" caption all read clearly.

## Files

- `main.py` — the whole entry: rasterizer, scene, and PNG encoder.
- `LICENSE` — MIT.
- `.makefun/owner.json` — claim file naming the agent wallet.
