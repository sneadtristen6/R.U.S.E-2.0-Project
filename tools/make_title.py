"""Draws the apps' title, "R.U.S.E. 2.0 PROJECT" in gold (the owner, 2026-10-22: "the in-game ruse, like on the menu
screen ... gold ... i want it to say Ruse 2.0 Project"), into the Studio's and the Launcher's pages (ui/title.svg).
Wide, heavy letters made of bars with narrow slots, a full stop as a small triangle tucked into a cut at the letter's
bottom right, shaded top to bottom, a dark rim and a drop shadow, in the style of the game's menu title; every shape
is ours (rectangles and triangles). Run it again after changing a shape:
    python -I tools/make_title.py [--preview <html file>]"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = [ROOT / "src" / app / "ui" / "title.svg" for app in ("ruse_studio", "ruse_launcher")]
H, S, T = 100, 32, 26          # letter height, upright stroke, bar thickness
GAP = (H - 3 * T) / 2          # the slot between three bars
WIDE, NARROW = 132, 112        # R.U.S.E.'s letters are wider than the rest, as the logo's
SPACE, WORD = 14, 46           # between letters, between words
NOTCH, DOT = 56, 34            # a full stop: the corner cut, and the triangle in it


def glyph(ch: str, w: float) -> tuple[list, list]:
    """(the letter's slots, as rectangles cut out of its w x H block; extra solid pieces)."""
    mid1, mid2 = T + GAP, 2 * T + GAP           # the middle bar's top and bottom
    if ch == "E":
        return [(S, T, w, mid1), (S, mid2, w, mid2 + GAP)], []
    if ch == "U":
        return [(S, 0, w - S, H - T)], []
    if ch == "S":
        return [(S, T, w, mid1), (0, mid2, w - S, mid2 + GAP)], []
    if ch == "2":
        return [(0, T, w - S, mid1), (S, mid2, w, mid2 + GAP)], []
    if ch in "0O":
        return [(S, T, w - S, H - T)], []
    if ch == "C":
        return [(S, T, w, H - T)], []
    if ch == "R":
        # a bowl over the middle bar, the stem down the left, and a leg slanting down to the right, its foot ending
        # before the corner a full stop cuts (the logo's R)
        foot = w - 26  # its right edge at the bottom: the corner cut trims it on the slant
        leg = [(w * 0.40, mid2), (w * 0.40 + S * 1.15, mid2), (foot, H), (foot - S * 1.15, H)]
        return [(S, T, w - S, mid1), (S, mid2, w, H)], [leg]
    if ch == "P":
        return [(S, T, w - S, mid1), (S, mid2, w, H)], []
    if ch == "J":
        return [(S, 0, w - S, H - T), (0, 0, S, H * 0.45)], []
    if ch == "T":
        return [(0, T, (w - S) / 2, H), ((w + S) / 2, T, w, H)], []
    raise ValueError(ch)


def layout(text: str):
    """[(the letter, x, width, followed by a full stop)], and the whole width."""
    out, x = [], 0.0
    i = 0
    first_word = True
    while i < len(text):
        ch = text[i]
        if ch == " ":
            x += WORD - SPACE
            first_word = False
            i += 1
            continue
        dot = i + 1 < len(text) and text[i + 1] == "."
        w = WIDE if first_word else NARROW
        out.append((ch, x, w, dot))
        x += w + SPACE
        i += 2 if dot else 1
    return out, x - SPACE


def svg(text: str = "R.U.S.E. 2.0 PROJECT") -> str:
    parts, width = layout(text)
    pad = 10
    vw, vh = width + 2 * pad, H + 2 * pad + 6
    mask = []
    for ch, x, w, dot in parts:
        ox, oy = x + pad, pad
        mask.append(f'<rect x="{ox:.1f}" y="{oy}" width="{w}" height="{H}" fill="#fff"/>')
        slots, extra = glyph(ch, w)
        for x0, y0, x1, y1 in slots:
            mask.append(f'<rect x="{ox + x0:.1f}" y="{oy + y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" fill="#000"/>')
        for poly in extra:
            pts = " ".join(f"{ox + px:.1f},{oy + py:.1f}" for px, py in poly)
            mask.append(f'<polygon points="{pts}" fill="#fff"/>')
        if dot:  # the corner cut, and the full stop's triangle in it
            bx, by = ox + w, oy + H
            mask.append(f'<polygon points="{bx - NOTCH},{by} {bx},{by - NOTCH} {bx},{by}" fill="#000"/>')
            mask.append(f'<polygon points="{bx - DOT},{by} {bx},{by - DOT} {bx},{by}" fill="#fff"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw:.0f} {vh:.0f}" role="img" aria-label="{text}">
  <defs>
    <linearGradient id="gold" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fff6d2"/><stop offset="0.38" stop-color="#f1c862"/>
      <stop offset="0.62" stop-color="#c9932e"/><stop offset="1" stop-color="#7a5414"/>
    </linearGradient>
    <mask id="letters" maskUnits="userSpaceOnUse">{"".join(mask)}</mask>
    <filter id="look" x="-5%" y="-20%" width="110%" height="150%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="1.6" result="soft"/>
      <feComponentTransfer in="soft" result="round"><feFuncA type="linear" slope="6" intercept="-2.6"/></feComponentTransfer>
      <feComposite in="SourceGraphic" in2="round" operator="in" result="shape"/>
      <feMorphology in="round" operator="dilate" radius="2.2" result="rimwide"/>
      <feFlood flood-color="#2b1a03" result="rimcolour"/><feComposite in="rimcolour" in2="rimwide" operator="in" result="rim"/>
      <feGaussianBlur in="rimwide" stdDeviation="3" result="blur"/><feOffset in="blur" dx="3" dy="5" result="drop"/>
      <feFlood flood-color="#000" flood-opacity="0.7"/><feComposite in2="drop" operator="in" result="shadow"/>
      <feMerge><feMergeNode in="shadow"/><feMergeNode in="rim"/><feMergeNode in="shape"/></feMerge>
    </filter>
  </defs>
  <g filter="url(#look)"><rect x="0" y="0" width="{vw:.0f}" height="{vh:.0f}" fill="url(#gold)" mask="url(#letters)"/></g>
</svg>
'''


title = svg()
for out in OUT:
    out.write_text(title, encoding="utf-8", newline="\n")
    print(out)
if "--preview" in sys.argv:  # the title on the apps' navy, big and at the header's height
    page = Path(sys.argv[sys.argv.index("--preview") + 1])
    page.write_text(f'''<!doctype html><meta charset="utf-8"><title>Title look</title>
<style>body{{margin:0;background:#0a1628;color:#f3f7fc;font:14px "Segoe UI";padding:24px}}
.big svg{{width:100%;height:auto}} .bar{{display:flex;align-items:center;gap:14px;background:#0f2038;padding:10px 16px;margin-top:28px}}
.bar svg{{height:30px}} .bar span{{color:#9db3cf}}</style>
<div class="big">{title}</div>
<div class="bar">{title}<span>Studio</span></div>
''', encoding="utf-8")
    print(page)
