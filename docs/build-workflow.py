#!/usr/bin/env python3
"""Build the team workflow page, the whole workflow on one HTML page.

What the page says about the workflow comes from skills/ask-team/SKILL.md (the
steps, how the router sizes a request, the ways in, the any-time skills, the
session and gate rules) and skills/ask-team/REGISTRY.md (every skill, where it
is used, what it does). SKILL.md speaks to Claude about "the user"; the page
turns that into "you". Change those two files, never the page:

    python3 docs/build-workflow.py                       # write docs/workflow.html to preview
    python3 docs/build-workflow.py --out _site/index.html
    python3 docs/build-workflow.py --check               # exit 1 when the sources can't be read,
                                                         # or a palette's text reads under 4.5:1

This file is the command line; the page is made in docs/workflow/:

    config.py    where the sources are, and the page's own frame: title, lede, glossary,
                 role names, palettes, fonts
    sources.py   reading SKILL.md, REGISTRY.md and the README's Install section
    render.py    the drawing helpers: voice, inline markdown, cards, arrows, links
    palettes.py  the palettes' CSS, and the check that their text reads at 4.5:1
    page.py      assembling the HTML
    page.css     the stylesheet; page.py fills in the palettes and the font faces
    theme.js     runs in the head: applies a pinned mode and palette before the page paints
    page.js      the bar, its appearance menu and the skills list

The page serves its own fonts from docs/fonts (SIL Open Font License, the licences
sit beside them), copied next to the page when it is written elsewhere, so no
visitor's browser asks a third party for anything.

GitHub Actions (.github/workflows/pages.yml) builds and publishes the page to
GitHub Pages on every push to main. skills/ask-team/scripts/check-registry.py
runs the --check.
"""
import hashlib
import os
import shutil
import sys

from workflow.config import FACES, FONTS, PREVIEW, README, REGISTRY, SKILL
from workflow.page import build
from workflow.palettes import palette_problems
from workflow.sources import SourceError, need, read_install, read_registry, read_router


def main():
    args = sys.argv[1:]
    try:
        router = read_router(SKILL)
        groups, kinds, sources = read_registry(REGISTRY, router['steps'])
        install = read_install(README)
        for _, file, _ in FACES:
            need(os.path.isfile(os.path.join(FONTS, file)), f'docs/fonts has no {file}')
    except SourceError as error:
        print(f'workflow page: cannot read the sources: {error}')
        return 1
    unreadable = palette_problems()
    if unreadable:
        print('workflow page: text under 4.5:1 in a palette:\n  ' + '\n  '.join(unreadable))
        return 1
    if '--check' in args:
        return 0
    out = args[args.index('--out') + 1] if '--out' in args else PREVIEW
    digest = hashlib.sha256(open(SKILL, 'rb').read() + open(REGISTRY, 'rb').read()).hexdigest()[:10]
    out_dir = os.path.dirname(os.path.abspath(out))
    os.makedirs(out_dir, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as page:
        page.write(build(router, groups, kinds, sources, install, digest))
    if out_dir != os.path.dirname(FONTS):
        shutil.copytree(FONTS, os.path.join(out_dir, 'fonts'), dirs_exist_ok=True)
    print(f'wrote {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
