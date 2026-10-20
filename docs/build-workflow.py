#!/usr/bin/env python3
"""Build the team workflow page, the whole workflow on one HTML page.

What the page says about the workflow comes from skills/ask-team/SKILL.md (the
steps, how the router sizes a request, the ways in, the any-time skills, the
session and gate rules) and skills/ask-team/REGISTRY.md (every skill, where it
is used, what it does). SKILL.md speaks to Claude about "the user"; the page
turns that into "you". The one sentence on each step's card is the page's own,
in docs/workflow/config.py: cards name no commands. Change those files, never
the page:

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
    page.js      the bar, its appearance menu, the skills list, and the step you are on
                 with /ask-team's answer for it

The page serves its own fonts from docs/fonts (SIL Open Font License, the licences
sit beside them), copied next to the page when it is written elsewhere, so no
visitor's browser asks a third party for anything.

The page names its version: the commit it was built from and that commit's date,
read from git, with "with local changes" when a tracked file differs from it.

docs/shoot.py screenshots or measures the built page in headless Chrome.

GitHub Actions (.github/workflows/pages.yml) builds and publishes the page to
GitHub Pages on every push to main. skills/ask-team/scripts/check-registry.py
runs the --check.
"""
import hashlib
import os
import shutil
import subprocess
import sys

# A planted change saved within the same second can otherwise run the old cached module.
sys.dont_write_bytecode = True

from workflow.config import FACES, FONTS, PREVIEW, README, REGISTRY, ROOT, SKILL, STEP_SUMMARIES
from workflow.page import build
from workflow.palettes import palette_problems, unchecked_backgrounds
from workflow.sources import SourceError, need, read_install, read_registry, read_router


def version():
    """The commit the page is built from: its short and full hash, its date, and whether
    tracked files have changes on top of it (the page being written is not one of them).
    None outside a git checkout."""
    def git(*args):
        return subprocess.run(['git', '-C', ROOT, *args], capture_output=True, text=True, check=True).stdout.strip()
    try:
        short, full, date = git('log', '-1', '--format=%h %H %cs').split()
        changed = bool(git('status', '--porcelain', '--untracked-files=no'))
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None
    return dict(short=short, full=full, date=date, changed=changed)


def main():
    args = sys.argv[1:]
    try:
        router = read_router(SKILL)
        groups, kinds, sources = read_registry(REGISTRY, router['steps'])
        install = read_install(README)
        need(sorted(STEP_SUMMARIES) == list(router['steps']),
             'docs/workflow/config.py: STEP_SUMMARIES should hold one sentence per Main flow step')
        for number, step in router['steps'].items():
            need('`' not in step['output'],
                 f'SKILL.md: step {number}\'s output names a command, which its card would show; '
                 'move it to the Command column')
        for _, file, _ in FACES:
            need(os.path.isfile(os.path.join(FONTS, file)), f'docs/fonts has no {file}')
    except SourceError as error:
        print(f'workflow page: cannot read the sources: {error}')
        return 1
    unchecked = unchecked_backgrounds()
    if unchecked:
        print('workflow page: page.css paints backgrounds the 4.5:1 check does not cover: '
              + ', '.join(f'--{name}' for name in unchecked)
              + '\n  add each to BACKGROUNDS or NO_TEXT_ON in docs/workflow/palettes.py')
        return 1
    unreadable = palette_problems()
    if unreadable:
        print('workflow page: text under 4.5:1 in a palette:\n  ' + '\n  '.join(unreadable))
        return 1
    if '--check' in args:
        return 0
    out = args[args.index('--out') + 1] if '--out' in args else PREVIEW
    built = version()
    digest = hashlib.sha256(open(SKILL, 'rb').read() + open(REGISTRY, 'rb').read()).hexdigest()[:10]
    out_dir = os.path.dirname(os.path.abspath(out))
    os.makedirs(out_dir, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as page:
        page.write(build(router, groups, kinds, sources, install, digest, built))
    if out_dir != os.path.dirname(FONTS):
        shutil.copytree(FONTS, os.path.join(out_dir, 'fonts'), dirs_exist_ok=True)
    print(f'wrote {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
