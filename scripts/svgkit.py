"""Shared pieces for the profile SVGs: theme tokens, text drawn as paths, icons.

Every word in every card is converted to vector outlines at build time. GitHub
serves README images with `Content-Security-Policy: default-src 'none'`, which
stops a font embedded in an SVG from loading, and system fonts differ between
machines. Outlines look the same everywhere, in the same Bricolage Grotesque
the portfolio site uses.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

import uharfbuzz as hb

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ICONS = ROOT / "icons"
FONTS = ROOT / "fonts"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

# Flat black and white, no gradients. The only colour is green: the
# availability dot and GitHub's own contribution scale.
THEMES = {
    "dark": {
        "bg": "#0a0a0a",
        "chip": "#141414",
        "border": "#262626",
        "hairline": "#1a1a1a",
        "grid": "#1c1c1c",
        "fg": "#fafafa",
        "muted": "#a3a3a3",
        "subtle": "#737373",
        "green": "#22c55e",
        "levels": ["#171717", "#0e4429", "#006d32", "#26a641", "#39d353"],
    },
    "light": {
        "bg": "#ffffff",
        "chip": "#ffffff",
        "border": "#e5e5e5",
        "hairline": "#f0f0f0",
        "grid": "#ededed",
        "fg": "#0a0a0a",
        "muted": "#525252",
        "subtle": "#737373",
        "green": "#16a34a",
        "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
    },
}

FAMILIES = {
    "sans": FONTS / "BricolageGrotesque.ttf",
    "mono": FONTS / "GeistMono.ttf",
}


# --------------------------------------------------------------------------
# Text as paths
# --------------------------------------------------------------------------

class _Pen:
    """Collects one glyph outline in font units (y axis pointing up)."""

    def __init__(self):
        self.ops = []

    def moveTo(self, p):
        self.ops.append(("M", p))

    def lineTo(self, p):
        self.ops.append(("L", p))

    def curveTo(self, a, b, c):
        self.ops.append(("C", a, b, c))

    def qCurveTo(self, a, b):
        self.ops.append(("Q", a, b))

    def closePath(self):
        self.ops.append(("Z",))

    def endPath(self):
        pass


@lru_cache(maxsize=None)
def _face(family):
    return hb.Face(hb.Blob.from_file_path(str(FAMILIES[family])))


def _opsz(family, size):
    # Matches `font-optical-sizing: auto` on the site: opsz follows the px size.
    return max(12, min(96, round(size))) if family == "sans" else 0


@lru_cache(maxsize=None)
def _font(family, wght, opsz):
    font = hb.Font(_face(family))
    axes = {"wght": wght}
    if family == "sans":
        axes.update(opsz=opsz, wdth=100)
    font.set_variations(axes)
    return font


@lru_cache(maxsize=None)
def _outline(family, wght, opsz, gid):
    pen = _Pen()
    _font(family, wght, opsz).draw_glyph_with_pen(gid, pen)
    return tuple(pen.ops)


def _shape(s, family, wght, size, features):
    font = _font(family, wght, _opsz(family, size))
    buf = hb.Buffer()
    buf.add_str(s)
    buf.guess_segment_properties()
    hb.shape(font, buf, features or {})
    return buf.glyph_infos, buf.glyph_positions


def _n(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def measure(s, size, *, family="sans", wght=400, tracking=0.0, features=None):
    """Advance width in px; tracking is in em, like CSS letter-spacing."""
    if not s:
        return 0.0
    _, pos = _shape(s, family, wght, size, features)
    upem = _face(family).upem
    return (sum(p.x_advance for p in pos) * size / upem
            + tracking * size * max(len(pos) - 1, 0))


# Glyphs drawn so far for the document being built: (family, wght, opsz, gid) -> (id, path).
# document() writes them into <defs> once and empties this, so each SVG
# carries one outline per distinct glyph and a short <use> per character.
_glyphs = {}


def _relative(ops):
    """Compact path data: integer font units, relative commands, no spare separators."""
    out, cx, cy, sx, sy = [], 0, 0, 0, 0
    for op, *pts in ops:
        if op == "Z":
            out.append("z")
            cx, cy = sx, sy
            continue
        pts = [(round(px), round(py)) for px, py in pts]
        nums = []
        for px, py in pts:
            nums += [px - cx, py - cy]
        out.append(op.lower() + "".join(f"{v}" if i == 0 or v < 0 else f" {v}" for i, v in enumerate(nums)))
        cx, cy = pts[-1]
        if op == "M":
            sx, sy = cx, cy
    return "".join(out)


def _glyph(family, wght, opsz, gid):
    key = (family, wght, opsz, gid)
    if key not in _glyphs:
        _glyphs[key] = (f"g{len(_glyphs)}", _relative(_outline(family, wght, opsz, gid)))
    return _glyphs[key]


def text(s, x, y, size, fill, *, family="sans", wght=400, anchor="start",
         tracking=0.0, features=None, attrs="", inline=False):
    """The outlines of `s` with the baseline at y.

    `inline=True` bakes every coordinate into one <path>, for text whose fill
    is a gradient in page coordinates (the <use> form is flipped and scaled).
    """
    infos, pos = _shape(s, family, wght, size, features)
    upem = _face(family).upem
    scale = size / upem
    width = measure(s, size, family=family, wght=wght, tracking=tracking, features=features)
    x -= {"start": 0, "middle": width / 2, "end": width}[anchor]
    opsz = _opsz(family, size)
    parts, pen_x = [], 0.0
    for info, p in zip(infos, pos):
        gx, gy = pen_x + p.x_offset, p.y_offset
        if inline:
            for op, *pts in _outline(family, wght, opsz, info.codepoint):
                parts.append(op + " ".join(
                    f"{_n(x + (gx + px) * scale)} {_n(y - (gy + py) * scale)}" for px, py in pts))
        else:
            gid, d = _glyph(family, wght, opsz, info.codepoint)
            if d:
                parts.append(f'<use href="#{gid}" x="{round(gx)}"' + (f' y="{round(gy)}"' if gy else "") + "/>")
        pen_x += p.x_advance + tracking * upem
    if inline:
        return f'<path d="{"".join(parts)}" fill="{fill}"{attrs}/>'
    return (f'<g transform="translate({_n(x)} {_n(y)}) scale({scale:.5g} {-scale:.5g})" '
            f'fill="{fill}"{attrs}>{"".join(parts)}</g>')


def wrap(s, size, max_width, **kw):
    lines, line = [], ""
    for word in s.split():
        trial = f"{line} {word}".strip()
        if line and measure(trial, size, **kw) > max_width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line] if line else lines


# --------------------------------------------------------------------------
# Colour
# --------------------------------------------------------------------------

def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return "#" + "".join(f"{round(c):02x}" for c in rgb)


def _luminance(h):
    def channel(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def mix(a, b, t):
    return _hex(tuple(x + (y - x) * t for x, y in zip(_rgb(a), _rgb(b))))


def legible(color, bg, toward, minimum=3.0):
    """Nudge a brand colour toward `toward` until it reads against `bg`.

    Near-black or near-white marks (Next.js, Vercel, Express) jump straight to
    the theme's text colour instead of turning a muddy grey.
    """
    if contrast(color, bg) >= minimum:
        return color
    r, g, b = _rgb(color)
    if max(r, g, b) - min(r, g, b) < 40:
        return toward
    for step in range(1, 11):
        c = mix(color, toward, step / 10)
        if contrast(c, bg) >= minimum:
            return c
    return toward


# --------------------------------------------------------------------------
# Icons
# --------------------------------------------------------------------------

_UNSAFE = {"script", "foreignObject", "image", "use", "a", "style"}


@lru_cache(maxsize=None)
def _icon_source(name):
    root = ET.parse(ICONS / f"{name}.svg").getroot()
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag in _UNSAFE or any(k.startswith("on") for k in el.attrib):
            raise ValueError(f"icons/{name}.svg contains <{tag}> or an event handler")
    outlined = root.get("stroke") == "currentColor"
    kids = [c for c in root if c.tag.split("}")[-1] not in {"title", "desc"}]
    inner = "".join(ET.tostring(c, encoding="unicode") for c in kids)
    inner = re.sub(r'\sxmlns(:\w+)?="[^"]*"', "", inner)
    return root.get("viewBox"), outlined, inner


def icon(name, x, y, size, color):
    view_box, outlined, inner = _icon_source(name)
    paint = (f'fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
             if outlined else f'fill="{color}"')
    inner = inner.replace("currentColor", color)
    return (f'<svg x="{_n(x)}" y="{_n(y)}" width="{_n(size)}" height="{_n(size)}" '
            f'viewBox="{view_box}" {paint}>{inner}</svg>')


# --------------------------------------------------------------------------
# Documents
# --------------------------------------------------------------------------

REDUCED_MOTION = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def document(width, height, title, desc, body, style=""):
    from html import escape
    css = f"<style>{style}{REDUCED_MOTION}</style>" if style else ""
    glyphs = "".join(f'<path id="{gid}" d="{d}"/>' for gid, d in _glyphs.values() if d)
    _glyphs.clear()
    return (f'<svg xmlns="{SVG_NS}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'role="img" aria-labelledby="t d" fill="none">'
            f'<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>'
            f"{css}" + (f"<defs>{glyphs}</defs>" if glyphs else "") + f"{body}</svg>\n")


def write(name, svg):
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / name).write_text(svg, encoding="utf-8")
