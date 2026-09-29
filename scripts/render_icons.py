"""Renders the AURORA mark to raster icons (favicon.ico, apple-icon.png, 512 px PNG).

The favicon is transparent (no tile) in a mid-tone palette; the Apple touch icon keeps a navy
tile because iOS fills transparency with black.

The geometry is the same as apps/web/src/components/brand/Logo.tsx: three arms (a cubic Bezier
rotated 0, 120 and 240 degrees about the centre and mirrored so they spiral clockwise outward)
around a warm core, on a 48-unit grid. Drawn at high resolution and downsampled.

Usage: uv run --no-sync python scripts/render_icons.py
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps/web/src/app"
BRAND = ROOT / "apps/web/public/brand"
ARM = [(31, 24), (35.2, 18.1), (20.9, -0.8), (6.7, 14)]
COLORS = [(165, 139, 255), (92, 200, 255), (62, 230, 196)]
CORE = (255, 226, 184)
# Mid-tone palette for transparent favicons: readable on light and dark browser tabs alike.
TAB_COLORS = [(124, 92, 240), (14, 150, 222), (13, 170, 140)]
TAB_CORE = (245, 158, 11)
BG = (5, 8, 15)


def bezier(p: list[tuple[float, float]], n: int = 400) -> list[tuple[float, float, float]]:
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = p
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t**2, t**3
        out.append((a * x0 + b * x1 + c * x2 + d * x3, a * y0 + b * y1 + c * y2 + d * y3, t))
    return out


def render(
    size: int,
    *,
    background: str,
    stroke: float,
    gradient: bool,
    pad: float = 0.0,
    colors: list[tuple[int, int, int]] = COLORS,
    core_color: tuple[int, int, int] = CORE,
) -> Image.Image:
    ss = 8  # supersampling
    big = size * ss
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    if background == "square":
        bg = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        ImageDraw.Draw(bg).rounded_rectangle(
            [0, 0, big - 1, big - 1], radius=int(big * 0.22), fill=(*BG, 255)
        )
        img.alpha_composite(bg)
    elif background == "full":  # iOS rounds the corners itself; transparent corners turn black
        img.paste((*BG, 255), (0, 0, big, big))
    inner = big * (1 - 2 * pad)
    scale = inner / 48
    off = big * pad

    def to_px(x: float, y: float, rot: float) -> tuple[float, float]:
        x = 48 - x  # mirror: arms spiral clockwise outward (Northern Hemisphere)
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        dx, dy = x - 24, y - 24
        xr, yr = 24 + dx * c - dy * s, 24 + dx * s + dy * c
        return off + xr * scale, off + yr * scale

    r = stroke * scale / 2
    for rot, color in zip((0, 120, 240), colors, strict=True):
        layer = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for x, y, t in reversed(bezier(ARM)):
            alpha = 1.0 if not gradient else (1.0 if t < 0.4 else 1.0 - (t - 0.4) / 0.6 * 0.88)
            px, py = to_px(x, y, rot)
            d.ellipse([px - r, py - r, px + r, py + r], fill=(*color, int(255 * alpha)))
        img.alpha_composite(layer)
    core = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    cx, cy = off + 24 * scale, off + 24 * scale
    cr = (5.0 if not gradient else 4.4) * scale
    ImageDraw.Draw(core).ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(*core_color, 255))
    img.alpha_composite(core)
    return img.resize((size, size), Image.Resampling.LANCZOS)


def main() -> None:
    small = [
        render(
            s, background="none", stroke=5.6, gradient=False, colors=TAB_COLORS, core_color=TAB_CORE
        )
        for s in (16, 32, 48)
    ]
    small[2].save(
        APP / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=small[:2]
    )
    render(180, background="full", stroke=4.4, gradient=True, pad=0.12).convert("RGB").save(
        APP / "apple-icon.png"
    )
    render(512, background="square", stroke=4.2, gradient=True, pad=0.11).save(
        BRAND / "aurora-icon-512.png"
    )
    print("wrote favicon.ico, apple-icon.png, aurora-icon-512.png")


if __name__ == "__main__":
    main()
