#!/usr/bin/env python3
"""Render-then-sample gate for criminal-case visualization output.

Static SVG analysis cannot catch every way a card turns black (missing fill,
dangling filter refs, CSS that never matched, renderer quirks). This is the
final backstop: render the HTML to PNG with the project's html2png, then sample
pixels. Large near-black regions = a black card slipped through = FAIL.

Usage:
    python3 render_pixel_check.py <input.html> [--keep-png] [--png=out.png]

Exit codes: 0 PASS, 1 FAIL (black region found), 2 setup/render error.

Rationale (rule 6): the user has confirmed they dislike dark/black boxes. A
chart that renders with a black card face is a hard failure, not a warning.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

HTML2PNG = Path.home() / ".claude/skills/html2png/scripts/html2png.js"

# A pixel is "near-black" below this perceived luminance (0..255).
NEAR_BLACK_LUM = 60
# Fail if a single horizontal band (row group) is >= this fraction near-black,
# OR the whole image exceeds the global fraction. Bands catch one black card
# even when the rest of the long page is white.
BAND_FRACTION = 0.45
GLOBAL_FRACTION = 0.06
BAND_ROWS = 40  # downsampled rows per band


def render(html: Path, png: Path, width: int) -> None:
    if not HTML2PNG.exists():
        raise FileNotFoundError(f"html2png not found at {HTML2PNG}")
    subprocess.run(
        ["node", str(HTML2PNG), str(html), str(png), f"--width={width}"],
        check=True,
        capture_output=True,
        text=True,
    )


def analyze(png: Path) -> tuple[bool, list[str]]:
    try:
        from PIL import Image
    except ImportError:
        return False, ["Pillow not installed; cannot pixel-check. pip install Pillow"]

    im = Image.open(png).convert("RGB")
    w, h = im.size
    # Downsample for speed; keep aspect. Width 200 is plenty to spot a card.
    small_w = 200
    small_h = max(1, int(h * small_w / w))
    sm = im.resize((small_w, small_h))
    px = list(sm.getdata())  # noqa: deprecation tolerated; small image

    def lum(p: tuple[int, int, int]) -> float:
        return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]

    near_black = [lum(p) < NEAR_BLACK_LUM for p in px]
    total = len(px)
    global_frac = sum(near_black) / total if total else 0.0

    msgs: list[str] = []
    failed = False

    if global_frac >= GLOBAL_FRACTION:
        failed = True
        msgs.append(
            f"global near-black coverage {global_frac*100:.1f}% "
            f">= {GLOBAL_FRACTION*100:.0f}% (rule 6: no dark/black cards)"
        )

    # Banded scan: find the worst horizontal band.
    rows = small_h
    band_px = small_w * min(BAND_ROWS, rows)
    worst = 0.0
    worst_y = 0
    for top in range(0, rows, BAND_ROWS):
        bottom = min(rows, top + BAND_ROWS)
        cnt = 0
        for y in range(top, bottom):
            base = y * small_w
            cnt += sum(near_black[base: base + small_w])
        frac = cnt / (small_w * (bottom - top))
        if frac > worst:
            worst, worst_y = frac, top
    if worst >= BAND_FRACTION:
        failed = True
        # Map band back to approximate original-y for the human.
        approx_y = int(worst_y / rows * h)
        msgs.append(
            f"horizontal band near y={approx_y}px is {worst*100:.0f}% near-black "
            f">= {BAND_FRACTION*100:.0f}% — looks like a black card. Open the PNG."
        )

    if not failed:
        msgs.append(
            f"OK: global near-black {global_frac*100:.1f}%, worst band {worst*100:.0f}%"
        )
    return (not failed), msgs


def main() -> int:
    ap = argparse.ArgumentParser(description="Render HTML and fail on black cards")
    ap.add_argument("html", type=Path)
    ap.add_argument("--png", type=Path, default=None)
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--keep-png", action="store_true")
    args = ap.parse_args()

    if not args.html.exists():
        print(f"ERROR: file not found: {args.html}")
        return 2

    tmp = None
    if args.png:
        png = args.png
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        png = Path(tmp.name)
        tmp.close()

    try:
        render(args.html, png, args.width)
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: render failed: {exc.stderr[:400]}")
        return 2
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 2

    ok, msgs = analyze(png)
    for m in msgs:
        prefix = "PASS" if ok and m.startswith("OK") else ("ERROR" if not ok else "INFO")
        print(f"{prefix}: {m}")

    if not args.keep_png and not args.png and png.exists():
        png.unlink()
    elif args.keep_png or args.png:
        print(f"INFO: PNG saved at {png}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
