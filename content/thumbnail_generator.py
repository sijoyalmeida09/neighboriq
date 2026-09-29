"""thumbnail_generator.py — YouTube thumbnail generator for NeighborIQ.

Generates 1280x720 branded thumbnails using Pillow.
Falls back gracefully if Pillow is not installed.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

log = logging.getLogger("thumbnail_generator")

ROOT = Path(__file__).resolve().parent.parent
THUMBNAILS_DIR = ROOT / "data" / "content"
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

BRAND_COLORS = {
    "bg_dark": (15, 17, 40),
    "bg_mid": (22, 33, 62),
    "accent_red": (233, 69, 96),
    "accent_gold": (255, 200, 55),
    "white": (255, 255, 255),
    "light_gray": (200, 200, 220),
    "dark_gray": (80, 90, 120),
}

_W, _H = 1280, 720


def _draw_gradient_bg(draw: object, img_width: int, img_height: int) -> None:
    """Draw a left-to-right dark gradient."""
    from PIL import ImageDraw  # type: ignore

    bg_dark = BRAND_COLORS["bg_dark"]
    bg_mid = BRAND_COLORS["bg_mid"]
    steps = img_width
    for x in range(steps):
        t = x / steps
        r = int(bg_dark[0] + (bg_mid[0] - bg_dark[0]) * t)
        g = int(bg_dark[1] + (bg_mid[1] - bg_dark[1]) * t)
        b = int(bg_dark[2] + (bg_mid[2] - bg_dark[2]) * t)
        draw.line([(x, 0), (x, img_height)], fill=(r, g, b))


def _load_font(size: int, bold: bool = False):  # type: ignore
    """Load a truetype font if available; fall back to PIL default."""
    try:
        from PIL import ImageFont  # type: ignore
        import os

        # Try common system font paths
        candidates: list[str] = []
        if os.name == "nt":  # Windows
            candidates = [
                r"C:\Windows\Fonts\arialbd.ttf",
                r"C:\Windows\Fonts\arial.ttf",
                r"C:\Windows\Fonts\calibrib.ttf",
            ]
        else:  # Linux/Mac
            candidates = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ]

        for path in candidates:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)

        return ImageFont.load_default()
    except Exception:
        try:
            from PIL import ImageFont  # type: ignore
            return ImageFont.load_default()
        except Exception:
            return None


def _draw_badge(draw: object, x: int, y: int, w: int, h: int, color: Tuple[int, int, int], text: str, font: object) -> None:
    """Draw a filled rounded-rectangle badge with centered text."""
    from PIL import ImageDraw  # type: ignore

    radius = 12
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=color)

    # Center text in badge
    try:
        bbox = font.getbbox(text) if hasattr(font, "getbbox") else (0, 0, len(text) * 10, 20)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
    except Exception:
        tw, th = len(text) * 10, 20

    tx = x + (w - tw) // 2
    ty = y + (h - th) // 2
    draw.text((tx, ty), text, font=font, fill=BRAND_COLORS["white"])


def generate_thumbnail(
    zip_code: str,
    city: str,
    niche: str,
    stat_line: str,
    demand_line: str,
    opportunity_score: int,
) -> Path | None:
    """
    Generates 1280x720 YouTube thumbnail.
    Returns path to saved PNG, or None if Pillow is not installed.
    """
    try:
        from PIL import Image, ImageDraw  # type: ignore
    except ImportError:
        log.warning("Pillow not installed — skipping thumbnail generation")
        return None

    try:
        img = Image.new("RGB", (_W, _H), BRAND_COLORS["bg_dark"])
        draw = ImageDraw.Draw(img)

        _draw_gradient_bg(draw, _W, _H)

        # ── accent strip on left edge ──────────────────────────────────────────
        draw.rectangle([0, 0, 8, _H], fill=BRAND_COLORS["accent_red"])

        # ── "HIDDEN OPPORTUNITY" badge — top left ──────────────────────────────
        badge_font = _load_font(28, bold=True)
        _draw_badge(draw, 32, 32, 360, 56, BRAND_COLORS["accent_red"], "★ HIDDEN OPPORTUNITY", badge_font)

        # ── Score badge — top right ────────────────────────────────────────────
        score_text = f"Score: {opportunity_score}"
        score_color = (
            (56, 161, 105) if opportunity_score >= 70
            else (214, 158, 46) if opportunity_score >= 55
            else (113, 128, 150)
        )
        _draw_badge(draw, _W - 200, 32, 168, 56, score_color, score_text, badge_font)

        # ── Main stat line (large, gold) ───────────────────────────────────────
        stat_font = _load_font(72, bold=True)
        # Wrap if too long
        max_chars = 22
        if len(stat_line) > max_chars:
            words = stat_line.split()
            lines: list[str] = []
            current = ""
            for word in words:
                if len(current) + len(word) + 1 <= max_chars:
                    current = f"{current} {word}".strip()
                else:
                    if current:
                        lines.append(current)
                    current = word
            if current:
                lines.append(current)
        else:
            lines = [stat_line]

        y_stat = 140
        for line in lines:
            draw.text((52, y_stat), line, font=stat_font, fill=BRAND_COLORS["accent_gold"])
            try:
                bbox = stat_font.getbbox(line) if hasattr(stat_font, "getbbox") else (0, 0, 600, 80)
                y_stat += (bbox[3] - bbox[1]) + 8
            except Exception:
                y_stat += 80

        # ── Demand line (medium, white) ────────────────────────────────────────
        demand_font = _load_font(48, bold=True)
        draw.text((52, y_stat + 16), demand_line, font=demand_font, fill=BRAND_COLORS["white"])

        # ── City + ZIP — bottom right ──────────────────────────────────────────
        location_font = _load_font(32)
        location_text = f"{city} · {zip_code}"
        draw.text((_W - 400, _H - 64), location_text, font=location_font, fill=BRAND_COLORS["light_gray"])

        # ── NeighborIQ watermark — bottom left ─────────────────────────────────
        wm_font = _load_font(26)
        draw.text((32, _H - 56), "NeighborIQ", font=wm_font, fill=BRAND_COLORS["dark_gray"])

        # ── Save ───────────────────────────────────────────────────────────────
        safe_niche = niche.replace(" ", "_").lower()
        path = THUMBNAILS_DIR / f"{zip_code}_{safe_niche}_thumb.png"
        img.save(str(path), "PNG", optimize=True)
        log.info("Saved thumbnail → %s", path)
        return path

    except Exception as exc:
        log.error("Thumbnail generation failed: %s", exc)
        return None
