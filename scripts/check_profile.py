#!/usr/bin/env python3
"""Check the README and its SVGs before they ship. Standard library only.

    python3 scripts/check_profile.py
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
MAX_BYTES = 120_000
BANNED = {"script", "foreignObject", "image", "iframe", "text", "tspan"}

errors = []
readme = (ROOT / "README.md").read_text(encoding="utf-8")

# Every <picture> pairs a dark and a light file that exist, and its <img> is the light one.
for block in re.findall(r"<picture>.*?</picture>", readme, re.S):
    dark = re.search(r'prefers-color-scheme: dark\)" srcset="([^"]+)"', block)
    light = re.search(r'prefers-color-scheme: light\)" srcset="([^"]+)"', block)
    img = re.search(r'<img src="([^"]+)" alt="([^"]*)"', block)
    if not (dark and light and img):
        errors.append(f"<picture> needs dark and light <source> tags and an <img> with alt text: {block[:80]}")
        continue
    if img.group(1) != light.group(1):
        errors.append(f"{img.group(1)}: the <img> fallback should be the light file, {light.group(1)}")
    if not img.group(2).strip():
        errors.append(f"{img.group(1)}: empty alt text")
    if dark.group(1).replace("-dark.", "-light.") != light.group(1):
        errors.append(f"{dark.group(1)} and {light.group(1)} are not a matching pair")

referenced = set(re.findall(r"assets/[\w.-]+\.svg", readme))
on_disk = {f"assets/{p.name}" for p in ASSETS.glob("*.svg")}
errors += [f"README points to a missing file: {a}" for a in sorted(referenced - on_disk)]
errors += [f"Unused asset (delete it or reference it): {a}" for a in sorted(on_disk - referenced)]

for path in sorted(ASSETS.glob("*.svg")):
    name = path.name
    raw = path.read_text(encoding="utf-8")
    if path.stat().st_size > MAX_BYTES:
        errors.append(f"{name}: {path.stat().st_size:,} bytes, over the {MAX_BYTES:,} budget")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        errors.append(f"{name}: not valid XML ({e})")
        continue
    if root.find("{http://www.w3.org/2000/svg}title") is None:
        errors.append(f"{name}: missing <title>")
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag in BANNED:
            # <text> is banned too: GitHub can't load fonts into README images,
            # so every word must be outlined by svgkit.text().
            errors.append(f"{name}: contains <{tag}>")
        for key, value in el.attrib.items():
            if key.startswith("on"):
                errors.append(f"{name}: event handler {key}")
            if key.endswith("href") and not value.startswith("#"):
                errors.append(f"{name}: external reference {value}")
    if "@keyframes" in raw and "prefers-reduced-motion" not in raw:
        errors.append(f"{name}: animates without a reduced-motion fallback")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"OK: {len(on_disk)} SVGs, {len(referenced) // 2} light/dark pairs, all text outlined.")
