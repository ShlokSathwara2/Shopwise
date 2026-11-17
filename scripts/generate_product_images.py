"""Generate deterministic editorial-style SVG artwork for every product.

The UCI dataset has no product photography. Rather than depending on remote
images, each product gets a generated still-life illustration whose palette is
derived from its category and whose composition is derived from its stock code.
Run: python scripts/generate_product_images.py
"""
from __future__ import annotations

import hashlib
import html
import math
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "backend" / "data" / "catalog.csv"
OUT = ROOT / "backend" / "static" / "products"
CATEGORY_OUT = ROOT / "backend" / "static" / "categories"

PALETTES = {
    "Kitchen & Dining": ("#EAD8C2", "#C56B45", "#4A2B20", "#F7EFE3"),
    "Home Decor": ("#DCE1D0", "#7D9070", "#2E3A2B", "#F5F3E8"),
    "Lighting": ("#F0DCB6", "#C8963E", "#3D2C18", "#FFF8E7"),
    "Textiles": ("#E8D3CC", "#B9756A", "#402A28", "#FBF1EC"),
    "Storage": ("#DDD6C3", "#8B8064", "#332F26", "#F7F3E8"),
    "Stationery": ("#D3DEE4", "#56798B", "#1F313D", "#F1F5F6"),
    "Bags & Accessories": ("#E8D2B7", "#A97742", "#3B2A1B", "#FAF2E6"),
    "Christmas": ("#CFD8C6", "#A33A2C", "#223427", "#F4F5EC"),
    "Festive & Gifts": ("#E5CED9", "#9A5576", "#3B2030", "#FBF0F5"),
    "Garden & Outdoor": ("#D7E0C7", "#5F7E48", "#293823", "#F3F6EA"),
    "Bath & Beauty": ("#DFD5E3", "#8B6F9B", "#33283D", "#F8F2FA"),
    "Kids & Toys": ("#F1DEB4", "#D28A3C", "#3A2A16", "#FEF7E7"),
    "Everyday Finds": ("#D8DEE2", "#6D7D88", "#2B343A", "#F4F7F8"),
}

ICONS = {
    "Kitchen & Dining": """
        <ellipse cx="300" cy="382" rx="112" ry="30" fill="none" stroke="{ink}" stroke-width="2.2" opacity=".28"/>
        <path d="M205 300h150v78c0 42-34 72-75 72s-75-30-75-72v-78z" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>
        <path d="M355 320h25c28 0 43 18 43 40s-15 41-43 41h-25" fill="none" stroke="{ink}" stroke-width="2.4"/>
        <path d="M238 268c-12-18 12-24 0-42M278 268c-12-18 12-24 0-42M318 268c-12-18 12-24 0-42" fill="none" stroke="{accent}" stroke-width="2.4" stroke-linecap="round" opacity=".8"/>
        <path d="M232 438c38 16 95 16 133 0" fill="none" stroke="{accent}" stroke-width="2" opacity=".7"/>
    """,
    "Home Decor": """
        <ellipse cx="300" cy="470" rx="120" ry="24" fill="{ink}" opacity=".12"/>
        <path d="M246 268h108c-4 56-18 94-54 150-36-56-50-94-54-150z" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>
        <path d="M300 268v150M266 300c8 30 20 58 34 84M334 300c-8 30-20 58-34 84" fill="none" stroke="{accent}" stroke-width="1.6" opacity=".75"/>
        <path d="M300 268c-6-42 18-72 54-82M300 268c-34-18-60-16-82 6" fill="none" stroke="{ink}" stroke-width="2"/>
        <path d="M354 186c18-4 30 4 34 20-16 6-30 0-34-20zM218 274c-14-8-20-20-14-34 14 6 20 18 14 34z" fill="{accent}" opacity=".85"/>
    """,
    "Lighting": """
        <ellipse cx="300" cy="480" rx="96" ry="20" fill="{ink}" opacity=".12"/>
        <path d="M238 270h124l34 100H204l34-100z" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>
        <path d="M300 370v92M270 466h60" fill="none" stroke="{ink}" stroke-width="2.6" stroke-linecap="round"/>
        <circle cx="300" cy="292" r="5" fill="{accent}"/>
        <path d="M188 410c22 34 62 52 112 52s90-18 112-52" fill="none" stroke="{accent}" stroke-width="1.8" opacity=".55"/>
        <path d="M176 438c30 40 76 60 124 60s94-20 124-60" fill="none" stroke="{accent}" stroke-width="1.2" opacity=".3"/>
    """,
    "Textiles": """
        <path d="M214 302c28-16 58-16 86 0s58 16 86 0v136c-28 16-58 16-86 0s-58-16-86 0V302z" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>
        <path d="M214 330c28-16 58-16 86 0s58 16 86 0M214 360c28-16 58-16 86 0s58 16 86 0M214 390c28-16 58-16 86 0s58 16 86 0M214 420c28-16 58-16 86 0s58 16 86 0" fill="none" stroke="{accent}" stroke-width="1.5" opacity=".5"/>
        <path d="M210 292v-16M230 296v-16M370 296v-16M390 292v-16M210 446v16M390 446v16" stroke="{ink}" stroke-width="2" stroke-linecap="round"/>
        <circle cx="300" cy="372" r="24" fill="{accent}" opacity=".16"/>
    """,
    "Storage": """
        <ellipse cx="300" cy="470" rx="120" ry="22" fill="{ink}" opacity=".12"/>
        <rect x="220" y="300" width="160" height="160" rx="4" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>
        <path d="M220 346h160M300 300v160M258 300v46M342 300v46" fill="none" stroke="{ink}" stroke-width="1.8"/>
        <rect x="278" y="380" width="44" height="18" rx="9" fill="{accent}" opacity=".8"/>
        <rect x="246" y="256" width="108" height="44" rx="3" fill="{paper}" stroke="{ink}" stroke-width="2"/>
        <path d="M246 278h108" stroke="{accent}" stroke-width="1.4" opacity=".65"/>
    """,
    "Stationery": """
        <path d="M234 458l15-68 140-142 54 52-140 142-69 16z" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>
        <path d="M252 390l54 52M389 248l54 52" fill="none" stroke="{ink}" stroke-width="2"/>
        <path d="M249 458l15-68 34 32-49 36z" fill="{accent}" opacity=".9"/>
        <path d="M248 410l12-58 54 52-32 38-34-32z" fill="none" stroke="{accent}" stroke-width="1.4" opacity=".6"/>
        <path d="M198 272h44M220 250v44M398 410h38M417 391v38" stroke="{accent}" stroke-width="2" stroke-linecap="round" opacity=".7"/>
    """,
    "Bags & Accessories": """
        <ellipse cx="300" cy="470" rx="112" ry="22" fill="{ink}" opacity=".12"/>
        <path d="M225 310h150l22 146H203l22-146z" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>
        <path d="M262 310v-26c0-22 17-38 38-38s38 16 38 38v26" fill="none" stroke="{ink}" stroke-width="2.4"/>
        <path d="M244 356h112M233 390h134" stroke="{accent}" stroke-width="1.4" opacity=".55"/>
        <circle cx="300" cy="404" r="5" fill="{accent}"/>
        <path d="M203 424c64 16 130 16 194 0" fill="none" stroke="{accent}" stroke-width="1.2" opacity=".35"/>
    """,
    "Christmas": """
        <path d="M300 214v244" stroke="{ink}" stroke-width="2"/>
        <path d="M300 250c-70 8-98 74-92 118 34-6 70-34 92-72 22 38 58 66 92 72 6-44-22-110-92-118z" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>
        <circle cx="300" cy="388" r="16" fill="{accent}" opacity=".85"/>
        <path d="M300 432l10 22 24 3-18 17 4 24-20-11-20 11 4-24-18-17 24-3 10-22z" fill="{accent}" opacity=".9"/>
        <circle cx="240" cy="302" r="4" fill="{accent}"/><circle cx="356" cy="286" r="4" fill="{accent}"/><circle cx="338" cy="338" r="4" fill="{accent}"/>
    """,
    "Festive & Gifts": """
        <ellipse cx="300" cy="470" rx="112" ry="22" fill="{ink}" opacity=".12"/>
        <rect x="218" y="322" width="164" height="132" rx="4" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>
        <rect x="204" y="290" width="192" height="42" rx="4" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>
        <path d="M300 290v164M300 290c-38 0-68-16-62-44 6-24 44-16 62 44zM300 290c38 0 68-16 62-44-6-24-44-16-62 44z" fill="none" stroke="{accent}" stroke-width="2.4"/>
        <path d="M232 356h136" stroke="{accent}" stroke-width="1.2" opacity=".3"/>
    """,
    "Garden & Outdoor": """
        <path d="M300 476V262" stroke="{ink}" stroke-width="2.4" stroke-linecap="round"/>
        <path d="M300 312c-56 4-86-34-84-80 50-2 80 32 84 80zM300 372c56 4 86-34 84-80-50-2-80 32-84 80zM300 428c-48 2-76-28-74-68 44-2 70 26 74 68z" fill="{paper}" stroke="{ink}" stroke-width="2.2"/>
        <path d="M300 312c-26-12-48-34-60-60M300 372c26-12 48-34 60-60M300 428c-22-10-40-28-50-50" fill="none" stroke="{accent}" stroke-width="1.4" opacity=".65"/>
        <path d="M258 476h84" stroke="{ink}" stroke-width="2" opacity=".3"/>
    """,
    "Bath & Beauty": """
        <ellipse cx="300" cy="474" rx="88" ry="18" fill="{ink}" opacity=".12"/>
        <rect x="252" y="302" width="96" height="164" rx="22" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>
        <rect x="282" y="252" width="36" height="54" rx="8" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>
        <path d="M318 270h38v18h-38" fill="none" stroke="{ink}" stroke-width="2.4" stroke-linejoin="round"/>
        <rect x="268" y="356" width="64" height="52" rx="4" fill="{accent}" opacity=".16"/>
        <path d="M276 382h48M300 366v32" stroke="{accent}" stroke-width="1.6"/>
        <circle cx="334" cy="330" r="4" fill="{accent}"/><circle cx="260" cy="338" r="3" fill="{accent}" opacity=".7"/>
    """,
    "Kids & Toys": """
        <rect x="212" y="342" width="86" height="86" rx="8" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>
        <rect x="310" y="342" width="86" height="86" rx="8" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>
        <circle cx="255" cy="385" r="9" fill="none" stroke="{accent}" stroke-width="2"/>
        <path d="M353 370l22 40h-44l22-40z" fill="none" stroke="{accent}" stroke-width="2" stroke-linejoin="round"/>
        <path d="M300 318c-6-36 16-58 44-64M300 318c-30-6-48-26-46-54" fill="none" stroke="{ink}" stroke-width="2"/>
        <circle cx="345" cy="252" r="5" fill="{accent}"/><circle cx="252" cy="262" r="5" fill="{accent}"/>
    """,
    "Everyday Finds": """
        <circle cx="300" cy="366" r="104" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>
        <path d="M300 296l22 48 52 6-38 36 10 52-46-26-46 26 10-52-38-36 52-6 22-48z" fill="none" stroke="{accent}" stroke-width="2.2" stroke-linejoin="round"/>
        <circle cx="300" cy="366" r="14" fill="{accent}" opacity=".24"/>
        <path d="M186 330c-10 30-10 60 0 90M414 330c10 30 10 60 0 90" fill="none" stroke="{accent}" stroke-width="1.4" opacity=".4"/>
    """,
}


def slugify(code: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", code.lower()).strip("-")


def build_svg(code: str, name: str, category: str, index: int) -> str:
    bg, accent, ink, paper = PALETTES.get(category, PALETTES["Everyday Finds"])
    h = int(hashlib.sha1(code.encode()).hexdigest(), 16)
    rot = (h % 9) - 4
    cx = 360 + (h % 120) - 60
    cy = 190 + ((h >> 8) % 100) - 50
    r = 86 + ((h >> 16) % 60)
    icon = ICONS.get(category, ICONS["Everyday Finds"]).format(ink=ink, accent=accent, paper=paper)
    initials = html.escape("".join(part[0] for part in name.split()[:2]).upper())
    label = html.escape(category.upper())

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="750" viewBox="0 0 600 750" role="img" aria-label="{html.escape(name)}">
  <defs>
    <linearGradient id="bg{index}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{bg}"/>
      <stop offset="100%" stop-color="{paper}"/>
    </linearGradient>
    <filter id="grain{index}">
      <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch"/>
      <feColorMatrix type="saturate" values="0"/>
      <feComponentTransfer><feFuncA type="linear" slope="0.06"/></feComponentTransfer>
    </filter>
    <filter id="soft{index}"><feGaussianBlur stdDeviation="18"/></filter>
  </defs>
  <rect width="600" height="750" fill="url(#bg{index})"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{accent}" opacity=".16" filter="url(#soft{index})"/>
  <circle cx="{cx - 150}" cy="{cy + 260}" r="{r // 2}" fill="{accent}" opacity=".08" filter="url(#soft{index})"/>
  <path d="M60 110h480" stroke="{ink}" stroke-width="1" opacity=".20"/>
  <path d="M60 640h480" stroke="{ink}" stroke-width="1" opacity=".20"/>
  <text x="60" y="78" font-family="Helvetica, Arial, sans-serif" font-size="14" letter-spacing="5" fill="{ink}" opacity=".72">SHOPWISE</text>
  <text x="540" y="78" font-family="Georgia, serif" font-size="14" fill="{ink}" opacity=".55" text-anchor="end">{html.escape(code)}</text>
  <text x="58" y="300" font-family="Georgia, serif" font-size="180" fill="{ink}" opacity=".07">{initials}</text>
  <g transform="rotate({rot} 300 380)">{icon}</g>
  <text x="60" y="690" font-family="Helvetica, Arial, sans-serif" font-size="13" letter-spacing="3.5" fill="{ink}" opacity=".62">{label}</text>
  <text x="540" y="690" font-family="Georgia, serif" font-size="17" fill="{ink}" opacity=".55" text-anchor="end">No. {index:03d}</text>
  <rect width="600" height="750" filter="url(#grain{index})" opacity=".5"/>
</svg>"""


def build_category_svg(name: str, count: int) -> str:
    bg, accent, ink, paper = PALETTES.get(name, PALETTES["Everyday Finds"])
    icon = ICONS.get(name, ICONS["Everyday Finds"]).format(ink=ink, accent=accent, paper=paper)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="1100" viewBox="0 0 900 1100" role="img" aria-label="{html.escape(name)}">
  <defs><linearGradient id="c" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{bg}"/><stop offset="100%" stop-color="{paper}"/></linearGradient></defs>
  <rect width="900" height="1100" fill="url(#c)"/>
  <circle cx="650" cy="260" r="220" fill="{accent}" opacity=".12"/>
  <circle cx="230" cy="830" r="160" fill="{accent}" opacity=".08"/>
  <text x="64" y="92" font-family="Helvetica, Arial, sans-serif" font-size="16" letter-spacing="6" fill="{ink}" opacity=".6">SHOPWISE / EDIT</text>
  <g transform="translate(150 180) scale(1.28) rotate(-3 300 380)">{icon}</g>
  <text x="64" y="950" font-family="Georgia, serif" font-size="58" fill="{ink}">{html.escape(name)}</text>
  <text x="66" y="1000" font-family="Helvetica, Arial, sans-serif" font-size="16" letter-spacing="4" fill="{ink}" opacity=".6">{count} PIECES</text>
</svg>"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CATEGORY_OUT.mkdir(parents=True, exist_ok=True)
    catalog = pd.read_csv(CATALOG)
    for i, row in catalog.iterrows():
        svg = build_svg(str(row["code"]), str(row["name"]), str(row["category"]), i + 1)
        (OUT / f"{slugify(str(row['code']))}.svg").write_text(svg, encoding="utf-8")

    counts = catalog["category"].value_counts().to_dict()
    for cat, count in counts.items():
        (CATEGORY_OUT / f"{slugify(cat)}.svg").write_text(build_category_svg(cat, int(count)), encoding="utf-8")

    placeholder = build_svg("NEW", "A new Shopwise piece", "Everyday Finds", 999)
    (OUT / "placeholder.svg").write_text(placeholder, encoding="utf-8")
    (ROOT / "backend" / "static" / "hero.svg").write_text(build_category_svg("Home Decor", 122), encoding="utf-8")
    print(f"generated {len(catalog)} product images + {len(counts)} category images -> {OUT}")


if __name__ == "__main__":
    main()
