#!/usr/bin/env python3
"""See the built workflow page in headless Chrome: a screenshot, or where elements sit.

    python3 docs/shoot.py --shot out.png                          # 1280x900, light system
    python3 docs/shoot.py --width 390 --dark --palette nord --at '#skills' --shot phone.png
    python3 docs/shoot.py --group-by moment --measure '.group h4 .role' --style padding-left
    python3 docs/shoot.py --root ../other-checkout --shot before.png  # build another copy

It builds the page from --root (this checkout by default) into a temporary folder, then loads
it in an iframe of the asked size, so any width works, under 500px too. Stored choices are
set before the page runs (--theme pins a mode, --dark sets the system's), scrolling to --at is
instant, so the shot never lands mid-scroll, and each run gets a fresh browser profile.

--measure prints every match of a selector as `selector [index] x y w h` in page pixels, plus
each --style property computed on it. Chrome must run outside the Claude Code sandbox. CHROME
overrides the browser's path."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = os.environ.get('CHROME', '/opt/google/chrome/chrome')

# The outer page sets the stored choices, loads the built page beside it, scrolls, measures,
# and writes what it found into #out, under the iframe so a screenshot never shows it.
FRAME = """<!doctype html><meta charset="utf-8">
<style>html,body{margin:0}iframe{border:0;display:block}</style>
<iframe id="f"></iframe><pre id="out"></pre>
<script>
const o = OPTIONS, f = document.getElementById('f'), out = [];
f.width = o.width; f.height = o.height;
for (const [key, value] of Object.entries(o.store)) localStorage.setItem(key, value);
f.onload = () => {
  const d = f.contentDocument, w = f.contentWindow;
  d.documentElement.style.scrollBehavior = 'auto';
  setTimeout(() => {
    if (o.at) {
      const t = d.querySelector(o.at);
      if (t) w.scrollTo({top: t.getBoundingClientRect().top + w.scrollY - o.offset, behavior: 'instant'});
      else out.push('no match for --at ' + o.at);
    }
    for (const sel of o.measure) {
      const all = d.querySelectorAll(sel);
      if (!all.length) out.push(sel + ' no match');
      all.forEach((el, i) => {
        const r = el.getBoundingClientRect(), cs = w.getComputedStyle(el);
        const css = o.style.map(p => p + '=' + cs.getPropertyValue(p)).join(' ');
        out.push(`${sel} [${i}] ${Math.round(r.left)} ${Math.round(r.top + w.scrollY)} ${Math.round(r.width)} ${Math.round(r.height)}${css ? ' ' + css : ''}`);
      });
    }
    document.getElementById('out').textContent = out.join('\\n') + '\\nDONE';
  }, 300);
};
f.src = 'index.html';
</script>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', default=ROOT, help='the checkout to build the page from')
    ap.add_argument('--width', type=int, default=1280)
    ap.add_argument('--height', type=int, default=900)
    ap.add_argument('--dark', action='store_true', help="a dark system; the page follows it unless --theme pins one")
    ap.add_argument('--theme', choices=['light', 'dark'], help='a pinned mode, as the menu stores it')
    ap.add_argument('--palette', help='a palette key from docs/workflow/config.py, e.g. nord')
    ap.add_argument('--group-by', choices=['role', 'moment', 'kind'], help="the skills list's grouping")
    ap.add_argument('--at', help='a selector to scroll to, its top just under the bar')
    ap.add_argument('--offset', type=int, default=70, help='room left above --at for the bar (70)')
    ap.add_argument('--shot', help='write a PNG screenshot here')
    ap.add_argument('--measure', action='append', default=[], metavar='SELECTOR')
    ap.add_argument('--style', action='append', default=[], metavar='PROPERTY')
    a = ap.parse_args()
    if not a.shot and not a.measure:
        ap.error('ask for --shot, --measure, or both')

    work = tempfile.mkdtemp(prefix='workflow-shoot-')
    try:
        built = subprocess.run([sys.executable, os.path.join(a.root, 'docs', 'build-workflow.py'),
                                '--out', os.path.join(work, 'index.html')], capture_output=True, text=True)
        if built.returncode:
            print(built.stdout + built.stderr, end='')
            return 1
        store = {k: v for k, v in (('theme', a.theme), ('palette', a.palette), ('group-by', a.group_by)) if v}
        options = dict(width=a.width, height=a.height, store=store, at=a.at, offset=a.offset,
                       measure=a.measure, style=a.style)
        with open(os.path.join(work, 'frame.html'), 'w', encoding='utf-8') as frame:
            frame.write(FRAME.replace('OPTIONS', json.dumps(options)))
        chrome = [CHROME, '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
                  '--allow-file-access-from-files', f'--user-data-dir={os.path.join(work, "profile")}',
                  '--virtual-time-budget=5000'] + (['--force-dark-mode'] if a.dark else [])
        url = 'file://' + os.path.join(work, 'frame.html')
        if a.measure:
            dom = subprocess.run(chrome + ['--dump-dom', url], capture_output=True, text=True, timeout=90).stdout
            found = dom.split('<pre id="out">', 1)[-1].split('</pre>', 1)[0]
            if 'DONE' not in found:
                print('workflow shoot: the page did not finish loading in Chrome')
                return 1
            print(found.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&').replace('\nDONE', '').replace('DONE', ''))
        if a.shot:
            # Chrome won't make a window under 500px wide; the iframe keeps the asked width,
            # and the shot is cropped back to it.
            shot = os.path.join(work, 'shot.png')
            subprocess.run(chrome + [f'--window-size={max(a.width, 500)},{a.height}', f'--screenshot={shot}', url],
                           capture_output=True, timeout=90)
            if not os.path.isfile(shot):
                print('workflow shoot: Chrome wrote no screenshot')
                return 1
            if a.width < 500:
                subprocess.run(['magick', shot, '-crop', f'{a.width}x{a.height}+0+0', '+repage', shot], check=True)
            shutil.copyfile(shot, a.shot)
            print(f'wrote {a.shot}')
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
