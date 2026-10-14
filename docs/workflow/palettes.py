"""The palettes: their CSS, and the build's check that their text reads at 4.5:1."""
import json

from .config import PALETTES

PAPERS = json.dumps({key: [light['paper'], dark['paper']] for key, _, light, dark in PALETTES})
TEXT = ['ink', 'muted', 'product', 'lead', 'dev', 'review', 'you']
# What each text colour sits on: the role colours on paper and cards; ink and muted also on
# the tray, which the skills toolbar shows through once it sticks.
BACKGROUNDS = {t: ('paper', 'surface', 'tray') if t in ('ink', 'muted') else ('paper', 'surface') for t in TEXT}


def tokens(palette):
    return ' '.join(f"--{name.replace('_', '-')}:{value};" for name, value in palette.items())


def palette_css():
    """Each palette's variables, for the page when it is picked and for its swatch in the menu.

    The page's own rules give Reader at :root, so a picked palette sets data-palette on
    html. Its light side is the default and its dark side outranks it, the way page.css
    does it for Reader: under a dark system unless light is pinned, or when dark is pinned.
    Swatches always carry their own palette, on whichever side the page shows."""
    css = []
    for key, _, light, dark in PALETTES:
        page = [] if key == 'reader' else [f':root[data-palette="{key}"]']
        swatch = f'[data-swatch="{key}"]'
        css.append(f'{", ".join(page + [swatch])}{{ {tokens(light)} }}')
        system = [f'{s}:not([data-theme="light"])' for s in page] + [f':root:not([data-theme="light"]) {swatch}']
        pinned = [f'{s}[data-theme="dark"]' for s in page] + [f':root[data-theme="dark"] {swatch}']
        css.append(f'@media (prefers-color-scheme: dark){{ {", ".join(system)}{{ {tokens(dark)} }} }}')
        css.append(f'{", ".join(pinned)}{{ {tokens(dark)} }}')
    return '\n'.join(css)


def contrast(a, b):
    """The WCAG contrast ratio of two #RRGGBB colours."""
    def lum(colour):
        rgb = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        r, g, b = (c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb)
        return .2126 * r + .7152 * g + .0722 * b
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + .05) / (lo + .05)


def palette_problems():
    """Every text colour that reads under 4.5:1 on the paper, cards or tray it sits on, and every
    step number that reads under 4.5:1 on its role colour."""
    problems = []
    for _, name, light, dark in PALETTES:
        for side, p in (('light', light), ('dark', dark)):
            for t in BACKGROUNDS:
                for bg in BACKGROUNDS[t]:
                    if contrast(p[t], p[bg]) < 4.5:
                        problems.append(f'{name} {side}: {t} {p[t]} on {bg} {p[bg]} is {contrast(p[t], p[bg]):.2f}:1')
            for t in TEXT[2:]:
                if contrast(p['on_role'], p[t]) < 4.5:
                    problems.append(f'{name} {side}: on_role {p["on_role"]} on {t} {p[t]} is {contrast(p["on_role"], p[t]):.2f}:1')
    return problems
