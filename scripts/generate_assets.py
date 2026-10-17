#!/usr/bin/env python3
"""Draw the static profile cards (hero, buttons, project cards, stack) in light and dark.

    pip install -r scripts/requirements.txt
    python3 scripts/generate_assets.py

The contribution graph has its own script because a workflow redraws it daily.
"""
from html import escape

from svgkit import THEMES, document, icon, legible, measure, text, wrap, write

SITE = "https://www.amritsapkota0.com.np"

BUTTONS = [
    # slug, label, icon, primary
    ("portfolio", "Portfolio", "lucide-globe", True),
    ("cv", "CV", "lucide-file-text", False),
    ("email", "Email", "lucide-mail", False),
    ("linkedin", "LinkedIn", "linkedin", False),
    ("instagram", "Instagram", "instagram", False),
]

# label: (icon file or None for a colour dot, brand colour)
BRANDS = {
    "TypeScript": ("typescript", "#3178C6"),
    "JavaScript": ("javascript", "#F7DF1E"),
    "HTML5": ("html5", "#E34F26"),
    "CSS": ("css", "#663399"),
    "React": ("react", "#61DAFB"),
    "Next.js": ("nextdotjs", "#000000"),
    "Tailwind CSS": ("tailwindcss", "#06B6D4"),
    "shadcn/ui": ("shadcnui", "#000000"),
    "Framer Motion": ("framer", "#0055FF"),
    "GSAP": ("gsap", "#0AE448"),
    "React Hook Form": ("reacthookform", "#EC5990"),
    "Zod": ("zod", "#408AFF"),
    "TanStack Table": ("tanstack", "#ECE8D1"),
    "Recharts": (None, "#22B5BF"),
    "Axios": ("axios", "#5A29E4"),
    "Node.js": ("nodedotjs", "#5FA04E"),
    "Express": ("express", "#000000"),
    "PostgreSQL": ("postgresql", "#4169E1"),
    "MongoDB": ("mongodb", "#47A248"),
    "Supabase": ("supabase", "#3FCF8E"),
    "Prisma": ("prisma", "#2D3748"),
    "Drizzle": ("drizzle", "#C5F74F"),
    "eSewa": (None, "#60BB46"),
    "Khalti": (None, "#5C2D91"),
    "Stripe": ("stripe", "#635BFF"),
    "PayPal": ("paypal", "#002991"),
    "Razorpay": ("razorpay", "#0C2451"),
    "Git": ("git", "#F03C2E"),
    "GitHub Actions": ("githubactions", "#2088FF"),
    "Vercel": ("vercel", "#000000"),
    "Netlify": ("netlify", "#00C7B7"),
    "Linux": ("linux", "#FCC624"),
    "PM2": ("pm2", "#2B037A"),
    "Figma": ("figma", "#F24E1E"),
}

# Only what the CV backs up. No test runners, Redux or Docker: none of them
# appear in the work repos, so they don't appear here either.
STACK = [
    ("Languages", ["TypeScript", "JavaScript", "HTML5", "CSS"]),
    ("Frontend", ["React", "Next.js", "Tailwind CSS", "shadcn/ui", "Framer Motion", "GSAP"]),
    ("Forms & data", ["React Hook Form", "Zod", "TanStack Table", "Recharts", "Axios"]),
    ("Backend", ["Node.js", "Express", "PostgreSQL", "MongoDB", "Supabase", "Prisma", "Drizzle"]),
    ("Payments", ["eSewa", "Khalti", "Stripe", "PayPal", "Razorpay"]),
    ("Ship & tools", ["Git", "GitHub Actions", "Vercel", "Netlify", "Linux", "PM2", "Figma"]),
]

WORK = [
    {
        "slug": "digital-patro",
        "kind": "WEB APP · YHHIT",
        "title": "Digital Patro",
        "desc": "Nepali calendar web app with a date converter, forex, gold and fuel prices, "
                "and embeddable widgets. I'm the main developer and lead the web project.",
        "tags": "Next.js · TypeScript · next-intl",
    },
    {
        "slug": "esewa-khalti",
        "kind": "OPEN SOURCE",
        "title": "eSewa + Khalti for Next.js",
        "desc": "A reference integration of Nepal's two everyday wallets, with payment "
                "handling kept on the server in Next.js 15 API routes.",
        "tags": "Next.js 15 · API routes · Vercel",
    },
    {
        "slug": "storefronts",
        "kind": "CLIENT WORK · YHHIT",
        "title": "E-commerce storefronts",
        "desc": "Yes Helping Hand, Gifty Point and Nepal Mountain Bike: catalogue, cart and "
                "multi-step checkout with eSewa and Khalti.",
        "tags": "Next.js · TypeScript · shadcn/ui",
    },
    {
        "slug": "portfolio",
        "kind": "PERSONAL",
        "title": "Portfolio + CMS",
        "desc": "My site and its own admin CMS on Supabase, with row-level security, "
                "JSON-LD and push-to-deploy to a VPS under PM2.",
        "tags": "Next.js 15 · Supabase · GitHub Actions",
    },
]

MOTION = (
    ".rise{animation:rise .9s cubic-bezier(.16,1,.3,1) both}"
    "@keyframes rise{from{opacity:0;transform:translateY(8px)}}"
    ".draw{stroke-dasharray:1;animation:draw 2.8s cubic-bezier(.65,0,.35,1) both}"
    "@keyframes draw{from{stroke-dashoffset:1}}"
    ".fade{animation:fade 1.4s ease both}"
    "@keyframes fade{from{opacity:0}}"
    ".halo{transform-box:fill-box;transform-origin:center;animation:halo 2.4s ease-out infinite}"
    "@keyframes halo{from{opacity:.55;transform:scale(1)}to{opacity:0;transform:scale(3)}}"
    ".ripple{animation:ripple 6s ease-in-out infinite alternate}"
    "@keyframes ripple{from{transform:translateX(-7px)}to{transform:translateX(7px)}}"
    ".star{animation:twinkle 3.6s ease-in-out infinite alternate}"
    "@keyframes twinkle{from{opacity:.15}}"
)


def delay(seconds):
    return f' style="animation-delay:{seconds}s"'


# --------------------------------------------------------------------------
# Hero
# --------------------------------------------------------------------------

def mountains(t, theme):
    """Machhapuchhre over the Annapurna ridge, as seen across Phewa Lake."""
    back = ("M548 214L566 202L582 191L596 172L607 160L616 165L627 148L638 157L649 141"
            "L662 160L676 173L700 182L748 176L766 152L780 133L791 143L804 124L818 141"
            "L832 160L848 176L866 188L880 196")
    # Both feet run down behind the hills so no stroke ends in mid-air.
    peak = ("M570 236L604 214L636 193L657 175L673 151L686 128L697 104L706 82L712 63L718 78"
            "L725 95L737 117L751 139L769 161L793 185L822 205L846 214L905 236")
    face = "M712 63L718 78L725 95L737 117L751 139L769 161L745 156L731 136L721 112L715 88Z"
    spine = "M712 63L709 92L703 121L696 146"
    hills = ("M540 240C572 222 604 214 640 222C676 230 700 212 742 213"
             "C786 214 812 232 846 226C860 223 872 220 880 219V246H540Z")
    lake = 242

    sky = [f'<circle cx="822" cy="74" r="58" fill="url(#sky-glow)"/>']
    if theme == "dark":
        sky.append('<mask id="crescent"><rect width="880" height="290" fill="#fff"/>'
                   '<circle cx="828" cy="69" r="13" fill="#000"/></mask>')
        sky.append(f'<circle cx="822" cy="74" r="14" fill="{t["sky_body"]}" mask="url(#crescent)" opacity=".9"/>')
        stars = [(612, 62, 1.1), (650, 96, .9), (758, 56, 1.2), (858, 128, .9),
                 (588, 116, .8), (776, 104, .8), (690, 44, 1)]
        for i, (x, y, r) in enumerate(stars):
            sky.append(f'<circle class="star" cx="{x}" cy="{y}" r="{r}" fill="#fafafa"{delay(i * .7)}/>')
    else:
        sky.append(f'<circle cx="822" cy="74" r="14" fill="{t["sky_body"]}" opacity=".9"/>')

    ripples = "".join(
        f'<path class="ripple" d="M{x} {y}h{w}" stroke="{t["subtle"]}" stroke-width="1" '
        f'stroke-linecap="round" opacity="{o}"{delay(i * .9)}/>'
        for i, (x, y, w, o) in enumerate([
            (602, 254, 46, .55), (676, 252, 72, .45), (780, 256, 40, .5),
            (630, 266, 64, .35), (724, 268, 30, .4), (584, 279, 34, .3), (680, 281, 52, .3),
        ]))
    snow = (f'<path class="fade" d="{peak}Z" fill="url(#snow)"{delay(1.8)}/>' if theme == "dark" else "")

    return f'''
<g mask="url(#scene-fade)">
  {"".join(sky)}
  <path class="draw" pathLength="1" d="{back}" stroke="{t["ridge"]}" stroke-width="1.3" stroke-linejoin="round"/>
  <path class="fade" d="{back}V236H548Z" fill="url(#ridge-fill)"{delay(1.6)}/>
  <path class="fade" d="{peak}Z" fill="{t["bg"]}"{delay(.4)}/>
  {snow}
  <path class="fade" d="{face}" fill="{t["peak"]}" opacity=".09"{delay(2)}/>
  <path class="draw" pathLength="1" d="{spine}" stroke="{t["peak"]}" stroke-width="1" opacity=".35"{delay(1.4)}/>
  <path class="draw" pathLength="1" d="{peak}" stroke="{t["peak"]}" stroke-width="1.6" stroke-linejoin="round"{delay(.3)}/>
  <path d="{hills}" fill="{t["hill"]}"/>
  <path d="M540 {lake}H880" stroke="{t["border"]}" stroke-width="1"/>
  {ripples}
</g>'''


def hero(theme):
    t = THEMES[theme]
    W, H = 880, 290
    glow_a, glow_b = t["glow_a"], t["glow_b"]
    name_end = "#ffffff" if theme == "dark" else "#3f3f46"
    name_stop = ('<stop offset=".35" stop-color="#ffffff"/><stop offset="1" stop-color="#ffffff" stop-opacity=".55"/>'
                 if theme == "dark" else
                 f'<stop offset=".35" stop-color="{t["fg"]}"/><stop offset="1" stop-color="{name_end}"/>')
    defs = f'''<defs>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  <radialGradient id="glow-a"><stop stop-color="{glow_a[0]}" stop-opacity="{glow_a[1]}"/><stop offset="1" stop-color="{glow_a[0]}" stop-opacity="0"/></radialGradient>
  <radialGradient id="glow-b"><stop stop-color="{glow_b[0]}" stop-opacity="{glow_b[1]}"/><stop offset="1" stop-color="{glow_b[0]}" stop-opacity="0"/></radialGradient>
  <linearGradient id="name" x1="0" y1="92" x2="0" y2="150" gradientUnits="userSpaceOnUse">{name_stop}</linearGradient>
  <linearGradient id="ridge-fill" x1="0" y1="124" x2="0" y2="214" gradientUnits="userSpaceOnUse">
    <stop stop-color="{t["ridge"]}" stop-opacity=".22"/><stop offset="1" stop-color="{t["ridge"]}" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="scene-x" x1="520" x2="640" gradientUnits="userSpaceOnUse">
    <stop stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/>
  </linearGradient>
  <radialGradient id="sky-glow"><stop stop-color="{t["sky_body"]}" stop-opacity="{.16 if theme == "dark" else .22}"/><stop offset="1" stop-color="{t["sky_body"]}" stop-opacity="0"/></radialGradient>
  <linearGradient id="snow" x1="0" y1="63" x2="0" y2="170" gradientUnits="userSpaceOnUse">
    <stop stop-color="{t["peak"]}" stop-opacity=".22"/><stop offset="1" stop-color="{t["peak"]}" stop-opacity="0"/>
  </linearGradient>
  <mask id="scene-fade"><rect width="{W}" height="{H}" fill="url(#scene-x)"/></mask>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".9" fill="{t["border"]}"/></pattern>
  <radialGradient id="dots-fade" cx="0.22" cy="0.1" r="0.75">
    <stop stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
  </radialGradient>
  <mask id="dots-mask"><rect width="{W}" height="{H}" fill="url(#dots-fade)"/></mask>
</defs>'''

    pill_label = "Available for work"
    pill_w = 40 + measure(pill_label, 13, wght=500)
    role, sep, place = "Frontend Developer", "·", "Pokhara, Nepal"
    role_w = measure(role, 21, wght=600)
    sep_x = 48 + role_w + 10
    place_x = sep_x + measure(sep, 21) + 10
    lines = wrap("I build fast, accessible web apps with Next.js and TypeScript, from e-commerce "
                 "storefronts and admin dashboards to payment flows.", 15, 440)

    left = f'''
<g class="rise"{delay(.05)}>
  <rect x="48.5" y="40.5" width="{pill_w:.1f}" height="29" rx="14.5" fill="{t["chip"]}" stroke="{t["border"]}"/>
  <circle class="halo" cx="65" cy="55" r="4" fill="{t["green"]}"/>
  <circle cx="65" cy="55" r="4" fill="{t["green"]}"/>
  {text(pill_label, 78, 59.6, 13, t["muted"], wght=500)}
</g>
<g class="rise"{delay(.15)}>{text("Amrit Sapkota", 45, 146, 68, "url(#name)", wght=800, tracking=-0.035, inline=True)}</g>
<g class="rise"{delay(.25)}>
  {text(role, 48, 188, 21, t["fg"], wght=600)}
  {text(sep, sep_x, 188, 21, t["subtle"])}
  {text(place, place_x, 188, 21, t["muted"])}
</g>
<g class="rise"{delay(.35)}>{"".join(text(line, 48, 224 + i * 23, 15, t["muted"]) for i, line in enumerate(lines))}</g>'''

    caption = text("MACHHAPUCHHRE · 6,993 M", 856, 276, 9.5, t["subtle"], family="mono", anchor="end", tracking=0.08)

    body = f'''{defs}
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="15.5" fill="{t["bg"]}"/>
<g clip-path="url(#card)">
  <circle cx="110" cy="-30" r="330" fill="url(#glow-a)"/>
  <circle cx="860" cy="330" r="360" fill="url(#glow-b)"/>
  <rect width="{W}" height="{H}" fill="url(#dots)" mask="url(#dots-mask)"/>
  {mountains(t, theme)}
  <g class="fade"{delay(2.4)}>{caption}</g>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="15.5" stroke="{t["border"]}"/>
{left}'''
    desc = ("Amrit Sapkota, Frontend Developer in Pokhara, Nepal, available for work. "
            "Builds fast, accessible web apps with Next.js and TypeScript. "
            "Line drawing of Machhapuchhre above Phewa Lake.")
    write(f"hero-{theme}.svg", document(W, H, "Amrit Sapkota", desc, body, MOTION))


# --------------------------------------------------------------------------
# Buttons
# --------------------------------------------------------------------------

def button(theme, slug, label, icon_name, primary):
    t = THEMES[theme]
    H, size = 40, 14
    W = round(14 + 16 + 8 + measure(label, size, wght=500) + 16)
    bg, fg, stroke = (t["fg"], t["bg"], t["fg"]) if primary else (t["chip"], t["fg"], t["border"])
    body = (f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{bg}" stroke="{stroke}"/>'
            + icon(icon_name, 14, 12, 16, fg)
            + text(label, 38, 25, size, fg, wght=500))
    write(f"btn-{slug}-{theme}.svg", document(W, H, label, f"{label} link", body))


# --------------------------------------------------------------------------
# Stack
# --------------------------------------------------------------------------

def chip(t, label, x, y):
    icon_name, brand = BRANDS[label]
    color = legible(brand, t["chip"], t["fg"])
    width = 10 + 14 + 7 + measure(label, 12.5, wght=500) + 11
    mark = (icon(icon_name, x + 10, y + 7, 14, color) if icon_name
            else f'<circle cx="{x + 17}" cy="{y + 14}" r="4.5" fill="{color}"/>')
    svg = (f'<rect x="{x + .5:.1f}" y="{y + .5}" width="{width - 1:.1f}" height="27" rx="7" '
           f'fill="{t["chip"]}" stroke="{t["border"]}"/>{mark}'
           + text(label, x + 31, y + 18.6, 12.5, t["fg"], wght=500))
    return svg, width


def stack(theme):
    t = THEMES[theme]
    W, cols, pad, gap = 880, 3, 22, 7
    col_w = W / cols
    panels, heights = [], []
    for i, (title, items) in enumerate(STACK):
        col, row = i % cols, i // cols
        x0 = col * col_w + pad
        x, y, parts = x0, 0, []
        for label in items:
            svg, w = chip(t, label, 0, 0)
            if x + w > x0 + col_w - 2 * pad and x > x0:
                x, y = x0, y + 28 + gap
            parts.append((label, x, y))
            x += w + gap
        heights.append(y + 28)
        panels.append((title, col, row, parts, len(items)))

    row_h = [max(h for i, h in enumerate(heights) if i // cols == r) + 72 for r in range(2)]
    H = sum(row_h)
    body = [f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{t["bg"]}" stroke="{t["border"]}"/>']
    body.append(f'<path d="M0 {row_h[0]}H{W}" stroke="{t["border"]}"/>')
    for c in range(1, cols):
        body.append(f'<path d="M{c * col_w:.1f} 0V{H}" stroke="{t["border"]}"/>')
    for n, (title, col, row, parts, count) in enumerate(panels):
        x0, y0 = col * col_w + pad, sum(row_h[:row])
        body.append(f'<g class="rise"{delay(.06 * n)}>')
        body.append(text(title, x0, y0 + 36, 14, t["fg"], wght=600))
        body.append(text(f"{count:02d}", x0 + col_w - 2 * pad, y0 + 36, 11, t["subtle"], family="mono", anchor="end"))
        for label, x, y in parts:
            body.append(chip(t, label, x, y0 + 52 + y)[0])
        body.append("</g>")
    style = (".rise{animation:rise .8s cubic-bezier(.16,1,.3,1) both}"
             "@keyframes rise{from{opacity:0;transform:translateY(6px)}}")
    desc = "Tech stack. " + " ".join(f"{title}: {', '.join(items)}." for title, items in STACK)
    write(f"stack-{theme}.svg", document(W, H, "Stack", desc, "".join(body), style))


# --------------------------------------------------------------------------
# Project cards
# --------------------------------------------------------------------------

def work_cards(theme):
    t = THEMES[theme]
    W, pad = 434, 26
    wrapped = {w["slug"]: wrap(w["desc"], 13.5, W - 2 * pad) for w in WORK}
    lines = max(len(v) for v in wrapped.values())
    rule = 100 + (lines - 1) * 20 + 24  # hairline sits under the last line of copy
    H = rule + 44
    glow = t["glow_a"]
    for w in WORK:
        body = f'''<defs>
  <clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath>
  <radialGradient id="g"><stop stop-color="{glow[0]}" stop-opacity="{glow[1] * .8:.2f}"/><stop offset="1" stop-color="{glow[0]}" stop-opacity="0"/></radialGradient>
</defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="13.5" fill="{t["bg"]}"/>
<circle cx="{W - 20}" cy="-10" r="170" fill="url(#g)" clip-path="url(#c)"/>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="13.5" stroke="{t["border"]}"/>
{text(w["kind"], pad, 38, 10, t["subtle"], family="mono", tracking=0.08)}
{icon("lucide-arrow-up-right", W - pad - 16, 25, 16, t["subtle"])}
{text(w["title"], pad, 72, 21, t["fg"], wght=700, tracking=-0.01)}
{"".join(text(line, pad, 100 + i * 20, 13.5, t["muted"]) for i, line in enumerate(wrapped[w["slug"]]))}
<path d="M{pad} {rule}H{W - pad}" stroke="{t["hairline"]}"/>
{text(w["tags"], pad, rule + 26, 11, t["subtle"], family="mono")}'''
        desc = f'{w["kind"].title()}. {w["desc"]} Built with {w["tags"].replace(" · ", ", ")}.'
        write(f"work-{w['slug']}-{theme}.svg", document(W, H, w["title"], desc, body))


if __name__ == "__main__":
    for theme in THEMES:
        hero(theme)
        for b in BUTTONS:
            button(theme, *b)
        stack(theme)
        work_cards(theme)
    print(f"Drew the hero, {len(BUTTONS)} buttons, {len(WORK)} project cards and the stack card, "
          f"in {len(THEMES)} themes.")
