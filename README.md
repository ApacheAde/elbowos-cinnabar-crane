# Cinnabar Crane

Full-colour Python 3 neon ingot-stacker for [ElbowOS](https://x.com/ElbowOS).

A kiln crane rides a rail and drops vermilion, gold, and copper ingots. Overhang is sheared. Perfect pours stack the combo. Miss the slab and the slag tumbles off.

Not a Nintendo ROM, not an emulator, and not a clone of the light-cycle, pipe-flow, or tide-hopper packs.

## Play

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 cinnabar_crane.py --play
```

Left / right or A / D slide the hook. Space drops. R refires the kiln.

## Record a 9:16 reel

```bash
python3 cinnabar_crane.py --record
```

Headless autoplay writes a 1080x1920, 15s, 30fps H.264 MP4 (libx264, yuv420p, CRF 20, +faststart).

## Links

* Featured account: https://x.com/ElbowOS
* Drive reel: https://drive.google.com/file/d/1Pal0NnOF-1nfBIuRmgE6sHhySDz4Hz9c/view?usp=drivesdk
* Posted copy: https://drive.google.com/file/d/14eX7Jb5_-vpAgThboDN7Ra0VMAfZr-bS/view?usp=drivesdk
