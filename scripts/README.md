# How the profile is drawn

Every image in the profile README is an SVG made by these scripts, in a light
and a dark version. GitHub picks one through `<picture>` to match the viewer's
theme.

| Script | Draws | When |
| --- | --- | --- |
| `generate_assets.py` | hero, buttons, project cards, stack | by hand, after editing its data |
| `update_contributions.py` | contribution graph | daily, by `.github/workflows/contributions.yml` |
| `check_profile.py` | nothing; checks README and SVGs | in the workflow, and before you push |

```sh
pip install -r scripts/requirements.txt
python3 scripts/generate_assets.py
GH_USER=amrit-sapkota GH_TOKEN=$(gh auth token) python3 scripts/update_contributions.py
python3 scripts/check_profile.py
```

`update_contributions.py --sample` draws made-up data if you only want a preview.

## Editing

- **Words, links, projects, stack:** the `BUTTONS`, `STACK`, `WORK` and
  `BRANDS` lists at the top of `generate_assets.py`. The README alt text
  repeats the card copy for screen readers, so update both.
- **Colours:** `THEMES` in `svgkit.py`. Flat black and white with no
  gradients; green is the only colour (availability dot, contribution graph).
- **New icon:** save the SVG in `icons/` (Simple Icons has most brands) and add
  it to `BRANDS`. Brand colours are nudged automatically when they would be
  too faint on the theme background.

## Why all text is outlines

GitHub serves README images with `Content-Security-Policy: default-src 'none'`,
so a font inside an SVG never loads, and `<text>` falls back to whatever font
the viewer's machine has. `svgkit.text()` shapes each string with HarfBuzz
using Bricolage Grotesque (the site's font) and writes the glyph outlines
instead. Each glyph is stored once per file and reused, which keeps a card at
20 to 80 KB. `check_profile.py` fails if a `<text>` element ever sneaks in.

Fonts are in `fonts/` under the SIL Open Font License, which allows this.
