#!/usr/bin/env python3
"""Build the team workflow page, the whole workflow on one HTML page.

Everything the page says comes from skills/ask-team/SKILL.md (the steps, how
the router sizes a request, the ways in, the any-time skills, the session and
gate rules) and skills/ask-team/REGISTRY.md (every skill, where it is used,
what it does). This script only draws them, so change those two files, never
the page:

    python3 docs/build-workflow.py                       # write docs/workflow.html to preview
    python3 docs/build-workflow.py --out _site/index.html
    python3 docs/build-workflow.py --check               # exit 1 when the sources can't be read

The page serves its own fonts from docs/fonts (SIL Open Font License, the licences
sit beside them), copied next to the page when it is written elsewhere, so no
visitor's browser asks a third party for anything.

GitHub Actions (.github/workflows/pages.yml) builds and publishes the page to
GitHub Pages on every push to main. skills/ask-team/scripts/check-registry.py
runs the --check.
"""
import hashlib
import html
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, 'skills', 'ask-team', 'SKILL.md')
REGISTRY = os.path.join(ROOT, 'skills', 'ask-team', 'REGISTRY.md')
PREVIEW = os.path.join(ROOT, 'docs', 'workflow.html')
FONTS = os.path.join(ROOT, 'docs', 'fonts')
REPO_URL = 'https://github.com/YannickBaudraz/claude-team-workflow'
PAGE_URL = 'https://yannickbaudraz.github.io/claude-team-workflow/'

TITLE = 'Claude Team Workflow'
LEDE = 'From an idea to a merged epic, run the way an engineering team works.'

# The router's Sessions section names these roles; the steps it leaves out are yours.
ROLE_WORDS = {'product': 'product', 'tech lead': 'lead', 'developer': 'dev', 'reviewer': 'review'}
ROLE_NAMES = {'product': 'Product', 'lead': 'Tech lead', 'dev': 'Developer',
              'review': 'Reviewer', 'you': 'You'}
GROUP_TITLES = {'start': 'Start here', 'in': 'Other ways in', 'any': 'Any time',
                'other': 'Outside the flow'}

LIGHT = dict(paper='#F2F4F7', surface='#FFFFFF', ink='#16202C', muted='#5B6778',
             rule='#D3DAE2', product='#94600F', lead='#0E7A70', dev='#2C5BC8',
             review='#7445C2', you='#C02E48', on_role='#FFFFFF')
DARK = dict(paper='#0F141A', surface='#17202A', ink='#E4E9EF', muted='#97A3B2',
            rule='#2B3644', product='#E3A64B', lead='#3FC2B3', dev='#82A5F6',
            review='#B898F2', you='#F27389', on_role='#0F141A')

# One variable woff2 per family, latin subset: (family, file, weight range).
FACES = [('Bricolage Grotesque', 'bricolage-grotesque.woff2', '600 700'),
         ('Instrument Sans', 'instrument-sans.woff2', '400 700'),
         ('JetBrains Mono', 'jetbrains-mono.woff2', '600 700')]
# The approval diamond, as the tab icon.
ICON = ('data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 16 16%22>'
        '<rect x=%223.5%22 y=%223.5%22 width=%229%22 height=%229%22 rx=%221%22 '
        'transform=%22rotate(45 8 8)%22 fill=%22%23C02E48%22/></svg>')

esc = html.escape


class SourceError(Exception):
    pass


def need(ok, message):
    if not ok:
        raise SourceError(message)


# ---- Reading the sources ------------------------------------------------------

def section(text, title):
    m = re.search(rf'^## {re.escape(title)}\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    need(m, f'SKILL.md has no "## {title}" section')
    return m.group(1).strip()


def sentences(text):
    text = ' '.join(text.split())
    return [s for s in re.split(r'(?<=[.!?])\s+(?=[A-Z`*])', text) if s]


def read_router(path):
    text = open(path, encoding='utf-8').read()
    text = re.sub(r'\A---\n.*?\n---\n', '', text, flags=re.S)
    intro = text.split('## How to route')[0]
    never = [s for s in sentences(intro) if 'never runs' in s]
    need(never, 'SKILL.md no longer says the router never runs the step')

    items = re.findall(r'^\d+\. \*\*(.+?)\*\*\s*(.*)$', section(text, 'How to route'), re.M)
    need(len(items) >= 2, 'How to route should be a numbered list with bold lead-ins')
    sizing = [rest for lead, rest in items if lead.lower().startswith('size')]
    need(sizing, 'How to route has no "Size the request" item')
    fork, fork_notes = [], []
    for s in sentences(sizing[0]):
        m = re.search(r'\*(\w+)\*', s)
        if m:
            fork.append((m.group(1).capitalize(), s))
        else:
            fork_notes.append(s)
    need(fork, 'Size the request names no sizes in *italics*')

    flow = section(text, 'Main flow')
    steps = {}
    for line in flow.splitlines():
        m = re.match(r'\|\s*(\d+)\s*\|(.*)\|\s*$', line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(2).split('|')]
        need(len(cells) == 3, f'Main flow row {m.group(1)} should have four columns')
        step, command, output = cells
        note = ''
        if '(' in step:
            step, note = step.split('(', 1)
            note = note.rstrip(')').strip()
        name, _, qual = (part.strip() for part in step.partition(','))
        steps[int(m.group(1))] = dict(
            n=int(m.group(1)), name=name, qual=qual, note=note,
            optional=note.lower().startswith('only'), command=command, output=output,
            # A gate is a step whose output has to be approved, or that you merge.
            gate=bool(re.search(r'\bapproved\b|\bmerges\b', output, re.I)))
    need(list(steps) == list(range(1, len(steps) + 1)), 'Main flow steps should be numbered 1, 2, 3...')

    rules_text = '\n'.join(l for l in flow.splitlines() if not l.startswith('|'))
    epics = re.search(r'about (\d+) epics per roadmap', rules_text)
    most = re.search(r'never more than (\d+)', rules_text)
    need(epics and most, 'Main flow no longer states the epics-per-roadmap preference')

    sessions = section(text, 'Sessions')
    roles = {}
    found = re.findall(r'\b(product|tech lead|developer|reviewer)\b[^()]*\((?:steps )?(\d+)(?: to (\d+))?',
                       ' '.join(sessions.split()))
    for word, lo, hi in found:
        for n in range(int(lo), int(hi or lo) + 1):
            roles[n] = ROLE_WORDS[word]
    need(set(roles.values()) == set(ROLE_WORDS.values()),
         'Sessions no longer names the product, tech lead, developer and reviewer steps')
    for n in steps:
        steps[n]['role'] = roles.get(n, 'you')

    per_epic = [n for n, s in steps.items() if s['qual'] == 'per epic']
    per_ticket = [n for n, s in steps.items() if s['qual'] == 'per ticket']
    need(per_epic and len(per_ticket) == 1,
         'Main flow should mark the epic steps "per epic" and the first ticket step "per ticket"')
    first, last, tick = min(per_epic), max(per_epic), per_ticket[0]
    need(last == max(steps) and first < tick < last,
         'The per-epic steps should close the flow and contain the per-ticket step')
    review = [n for n in range(tick, last) if steps[n]['role'] == 'review']
    need(review, 'No reviewer step inside the ticket loop')

    return dict(
        never=never[0], beats=[lead.rstrip('.') for lead, _ in items], fork=fork,
        fork_notes=fork_notes, steps=steps, epics=epics.group(1), most=most.group(1),
        project=[n for n in steps if n < first], lead=list(range(first, tick)),
        ticket=list(range(tick, last)), close=last, review=review[0],
        ways=[l[2:].strip() for l in section(text, 'Ways in').splitlines() if l.startswith('- ')],
        any_time=re.findall(r'`([^`]+)`(?: \(([^)]*)\))?', section(text, 'Any time')),
        gate_rules=sentences(rules_text), session_rules=sentences(sessions))


def read_registry(path, steps):
    tables, header = [], None
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if not line.startswith('|'):
            header = None
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if header is None:
            header = [c.lower() for c in cells]
            tables.append([])
        elif not all(set(c) <= set('-: ') for c in cells):
            tables[-1].append(dict(zip(header, cells)))
    workflow = [t for t in tables if t and 'does' in t[0]]
    need(len(workflow) == 1, 'REGISTRY.md should have one table with a Does column')

    groups = {}
    for row in workflow[0]:
        name, used, does = row['command'].strip('`'), row.get('used at', ''), row.get('does', '')
        need(does, f'REGISTRY.md: {name} has no Does')
        m = re.match(r'(\d+)\b[^,]*(?:,\s*(.*))?$', used)
        if m:
            key, tag = int(m.group(1)), m.group(2) or ''
            need(key in steps, f'REGISTRY.md: {name} is used at step {key}, which the router does not have')
        else:
            for key, word in (('start', 'entry point'), ('in', 'way in'), ('any', 'any time')):
                if word in used:
                    tag = used.replace(word, '').strip(' ,;')
                    break
            else:
                key, tag = 'other', used
        groups.setdefault(key, []).append((name, tag, does))
    need('start' in groups, 'REGISTRY.md has no "entry point" skill')
    return groups


# ---- Drawing ------------------------------------------------------------------

def md(s):
    """Inline markdown to HTML: `code` (command arguments dropped), **bold**, *italics*."""
    out = []
    for seg in re.split(r'(`[^`]*`)', s):
        if len(seg) > 1 and seg[0] == seg[-1] == '`':
            code = seg[1:-1]
            if code.startswith('/'):
                code = code.split(' <')[0]
            out.append(f'<code>{esc(code)}</code>')
        else:
            t = esc(seg)
            t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
            t = re.sub(r'\*(.+?)\*', r'<em>\1</em>', t)
            out.append(t)
    return ''.join(out)


def cap(s):
    return s[:1].upper() + s[1:]


def shown_output(output):
    """The output without sentences that only say it is approved: the gate mark says that."""
    keep = [s for s in sentences(output)
            if not re.fullmatch(r'(both )?approved( by the user)?\.?', s, re.I)]
    return ' '.join(keep)


ARR = '<span class="arr" aria-hidden="true"></span>'


def card_html(s, level=3):
    label = ROLE_NAMES[s['role']] + (f' · {s["qual"]}' if s['qual'] else '')
    note = f'<p class="note">{md(cap(s["note"]))}</p>' if s['note'] else ''
    out = shown_output(s['output'])
    result = (f'<p class="out">{md(out)}</p>' if out else '') + (
        '<p class="gate-mark"><span class="dia"></span>You approve</p>' if s['gate'] else '')
    return (f'<article class="card{" optional" if s["optional"] else ""} p-{s["role"]}" id="step-{s["n"]}">'
            f'<div class="card-head"><span class="num">{s["n"]}</span>'
            f'<span class="role">{esc(label)}</span></div>'
            f'<h{level} class="title"><a href="#skills-{s["n"]}">{esc(s["name"])}</a></h{level}>{note}'
            f'<p class="cmd-text">{md(s["command"])}</p>'
            + (f'<div class="result">{result}</div>' if result else '') + '</article>')


def flow_html(r, numbers, cls='flow', level=3):
    return f'<div class="{cls}">' + ARR.join(card_html(r['steps'][n], level) for n in numbers) + '</div>'


def page_css():
    def tokens(p):
        return ' '.join(f"--{k.replace('_', '-')}:{v};" for k, v in p.items())
    faces = ''.join(f'@font-face{{font-family:"{f}";src:url("fonts/{file}") format("woff2");'
                    f'font-weight:{w};font-style:normal;font-display:swap}}\n'
                    for f, file, w in FACES)
    return faces + f"""
/* Layout: one column of bands. The epic loop is a dashed frame whose rows snake,
   design to tickets leftwards and build to retro rightwards, so the retro sits under
   the first epic step. Below 1100px the flow stacks in reading order, and below 980px
   the router, sizes and panels do too. */
:root{{ {tokens(LIGHT)}
  --display:"Bricolage Grotesque","Segoe UI",system-ui,sans-serif;
  --body:"Instrument Sans","Segoe UI",system-ui,-apple-system,sans-serif;
  --mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
@media (prefers-color-scheme: dark){{ :root:not([data-theme="light"]){{ {tokens(DARK)} color-scheme:dark; }} }}
:root[data-theme="dark"]{{ {tokens(DARK)} color-scheme:dark; }}
*,*::before,*::after{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--body);font-size:.9375rem;line-height:1.5}}
.wrap{{max-width:1180px;margin:0 auto;padding-inline:clamp(16px,4vw,40px);padding-block:40px 64px;display:grid;gap:28px}}
h1,h2,h3,h4{{font-family:var(--display);text-wrap:balance;margin:0;line-height:1.15}}
h1{{font-size:clamp(1.875rem,5vw,2.875rem);font-weight:700;letter-spacing:-.01em}}
.lede{{color:var(--muted);font-size:1.0625rem;max-width:62ch;margin:10px 0 0}}
code{{font-family:var(--mono);font-size:.84em;font-weight:600;overflow-wrap:anywhere}}
a{{color:inherit;text-underline-offset:.18em}}
::selection{{background:var(--dev);color:var(--on-role)}}
a:focus-visible{{outline:2px solid var(--dev);outline-offset:2px;border-radius:3px}}
.legend{{display:flex;flex-wrap:wrap;gap:8px 20px;list-style:none;padding:0;margin:16px 0 0;font-size:.8438rem}}
.legend li{{display:flex;align-items:center;gap:7px}}
.sw{{width:11px;height:11px;border-radius:3px;background:var(--c)}}
.dia{{width:9px;height:9px;background:var(--you);transform:rotate(45deg);flex:none;display:inline-block}}
.dash-sw{{width:22px;height:12px;border:1.5px dashed var(--muted);border-radius:3px}}
.kicker{{font-family:var(--body);line-height:1.5;font-size:.75rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin:0}}
.box{{background:var(--surface);border:1px solid var(--rule);border-radius:12px}}
.router{{display:grid;grid-template-columns:minmax(0,280px) minmax(0,1fr);gap:20px;padding:20px 22px;align-items:center}}
.router .cmd{{font-family:var(--mono);font-size:1.875rem;font-weight:700;margin:4px 0}}
.router .sub{{color:var(--muted);margin:0;font-size:.8438rem}}
.router .sub strong{{color:var(--ink)}}
.beats{{display:flex;align-items:stretch;list-style:none;margin:0;padding:0}}
.beats li{{flex:1 1 0;min-width:0;background:var(--paper);border-radius:8px;padding:14px;font-weight:700;font-size:.9375rem;display:flex;align-items:center}}
.beats .arr{{flex:0 0 32px;background:none;padding:0;justify-content:center}}
.fork{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}}
.fork .box{{padding:16px 18px;display:grid;gap:6px;align-content:start}}
.fork p{{margin:0}}
.fork em{{font-style:normal;font-weight:700}}
.fork-note{{grid-column:1/-1;color:var(--muted);font-size:.8438rem;margin:-8px 0 0}}
.band{{display:grid;gap:12px}}
.flow{{display:flex;align-items:stretch}}
.flow-rev{{flex-direction:row-reverse}}
.arr{{flex:0 0 26px;display:flex;justify-content:center;padding-top:16px;color:var(--muted);font-size:1.125rem;font-weight:700}}
.arr::before{{content:"→"}}
.flow-rev > .arr::before{{content:"←"}}
.card{{flex:1 1 0;min-width:0;background:var(--surface);border:1px solid var(--rule);border-radius:10px;padding:14px;display:flex;flex-direction:column;gap:8px}}
.card.optional{{border-style:dashed;border-color:var(--muted)}}
.card-head{{display:flex;align-items:center;gap:9px}}
.num{{width:26px;height:26px;border-radius:6px;background:var(--c);color:var(--on-role);display:grid;place-items:center;font-weight:700;font-size:.8125rem;flex:none;font-variant-numeric:tabular-nums}}
.role{{font-size:.7188rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--c)}}
.card .title{{font-size:1.0625rem;font-weight:700}}
.card .title a{{text-decoration:none}}
.card .title a:hover{{text-decoration:underline}}
.note{{margin:-4px 0 0;color:var(--muted);font-size:.8125rem;line-height:1.4}}
.cmd-text{{margin:0;font-size:.8438rem;line-height:1.5}}
.cmd-text code{{font-size:.7812rem}}
.result{{margin-top:auto;padding-top:9px;border-top:1px solid var(--rule);display:grid;gap:8px}}
.out{{margin:0;font-weight:600;font-size:.8438rem;line-height:1.4}}
.out::before{{content:"→ ";color:var(--muted)}}
.gate-mark{{margin:0;display:flex;align-items:center;gap:8px;color:var(--you);font-weight:700;font-size:.7812rem}}
.frame{{border:1.5px dashed var(--muted);border-radius:16px;padding:26px 20px 18px;position:relative;display:grid}}
.frame > .kicker{{position:absolute;top:-9px;left:16px;background:var(--paper);padding:0 7px}}
.joint{{display:flex;justify-content:space-between;padding:10px 0;color:var(--muted);font-weight:700}}
.joint span{{width:25%;text-align:center}}
.joint .up{{color:var(--ink);font-size:.8438rem}}
.into-epic{{display:flex;justify-content:flex-end;margin:-14px 0;padding-right:9%;color:var(--muted);font-size:1.125rem;font-weight:700}}
.ticket-row{{display:flex;align-items:stretch}}
.ticket-row > .card{{flex:1 1 0}}
.ticket{{flex:3 1 0;min-width:0;border:1.5px dashed var(--muted);border-radius:12px;padding:20px 12px 12px;position:relative}}
.ticket > .kicker{{position:absolute;top:-9px;left:14px;background:var(--paper);padding:0 7px}}
.loop-note{{margin:10px 0 0;font-size:.8125rem;font-weight:700;display:flex;gap:6px;align-items:center}}
.loop-note::before{{content:"↺";color:var(--muted);font-size:1rem}}
.epic-note{{margin:14px 0 0;color:var(--muted);font-size:.8438rem}}
.panels{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:32px;padding-top:8px}}
.panels h2{{font-size:1.25rem;margin-bottom:12px}}
.panels ul{{list-style:none;margin:0;padding:0;display:grid;gap:12px}}
.panels li p{{margin:0}}
.panels .when{{color:var(--muted);font-size:.875rem}}
.rules li{{display:grid;grid-template-columns:16px minmax(0,1fr);gap:6px;align-items:start;font-size:.9062rem}}
.rules .dot{{width:7px;height:2px;background:var(--muted);margin-top:11px}}
.rules .dia{{margin-top:7px}}
.skills{{border-top:1px solid var(--rule);padding-top:36px;display:grid;gap:14px}}
.skills h2{{font-size:clamp(1.5rem,3.4vw,1.875rem)}}
.groups{{columns:3 300px;column-gap:36px;margin-top:10px}}
.group{{break-inside:avoid;margin:0 0 26px;scroll-margin-top:16px}}
.group h3{{font-size:1.0625rem;display:flex;align-items:center;gap:9px;margin-bottom:10px}}
.group .num{{width:24px;height:24px;font-size:.75rem;border-radius:5px}}
.group ul{{list-style:none;margin:0;padding:0;display:grid;gap:10px}}
.group li p{{margin:2px 0 0;color:var(--muted);font-size:.875rem;line-height:1.45}}
.group li > code{{font-size:.8125rem}}
.tag{{display:inline-block;margin-left:6px;padding:1px 6px;border-radius:4px;background:var(--surface);border:1px solid var(--rule);color:var(--muted);font-size:.7188rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase;vertical-align:1px}}
.foot{{color:var(--muted);font-size:.8125rem;margin:0}}
.foot code{{font-size:.75rem}}
.p-product{{--c:var(--product)}} .p-lead{{--c:var(--lead)}} .p-dev{{--c:var(--dev)}} .p-review{{--c:var(--review)}} .p-you{{--c:var(--you)}}
@media (max-width: 1100px){{
  .flow,.flow-rev,.ticket-row{{flex-direction:column}}
  .flow > .arr,.ticket-row > .arr{{padding:6px 0;flex-basis:auto}}
  .flow > .arr::before,.ticket-row > .arr::before{{content:"↓"}}
  .joint{{display:none}}
  .joint.phone{{display:flex;justify-content:center}}
  .into-epic{{justify-content:center;padding-right:0;margin:-18px 0}}
  .ticket{{margin:12px 0 0}}
}}
@media (min-width: 1101px){{ .joint.phone{{display:none}} }}
@media (max-width: 980px){{
  .router{{grid-template-columns:minmax(0,1fr)}}
  .beats{{flex-direction:column}}
  .beats .arr{{padding:4px 0}}
  .beats .arr::before{{content:"↓"}}
  .fork,.panels{{grid-template-columns:minmax(0,1fr)}}
  .fork-note{{margin:0}}
}}
"""


def build(router, groups, digest):
    r = router
    steps = r['steps']
    start = groups['start'][0][0]
    legend = ''.join(f'<li class="p-{k}"><span class="sw"></span>{esc(v)}</li>'
                     for k, v in ROLE_NAMES.items())
    legend += ('<li><span class="dia"></span>Your approval</li>'
               '<li><span class="dash-sw"></span>Only when needed</li>')
    beats = '<li class="arr" aria-hidden="true"></li>'.join(f'<li>{esc(b)}</li>' for b in r['beats'])
    fork = ''.join(f'<div class="box"><p class="kicker">{esc(k)}</p><p>{md(s)}</p></div>'
                   for k, s in r['fork'])
    fork += ''.join(f'<p class="fork-note">{md(s)}</p>' for s in r['fork_notes'])
    ways = ''.join(f'<li><p>{md(w)}</p></li>' for w in r['ways'])
    # A skill the router lists without a gloss gets its registry line.
    does = {n.lstrip('/'): d for entries in groups.values() for n, _, d in entries}
    any_time = ''.join(f'<li><p><code>{esc(n)}</code></p>'
                       f'<p class="when">{md(cap(w or does.get(n.lstrip("/"), "")))}</p></li>'
                       for n, w in r['any_time'])
    rules = ''.join(f'<li><span class="{"dia" if i == 0 else "dot"}"></span><span>{md(s)}</span></li>'
                    for i, s in enumerate(r['gate_rules']))
    rules += ''.join(f'<li><span class="dot"></span><span>{md(s)}</span></li>' for s in r['session_rules'])

    order = ['start'] + sorted(k for k in groups if isinstance(k, int)) + ['in', 'any', 'other']
    blocks = []
    for key in order:
        if key not in groups:
            continue
        if isinstance(key, int):
            s = steps[key]
            head = f'<h3 class="p-{s["role"]}"><span class="num">{key}</span>{esc(s["name"])}</h3>'
        else:
            head = f'<h3>{esc(GROUP_TITLES[key])}</h3>'
        items = ''.join(f'<li><code>{esc(n)}</code>'
                        + (f'<span class="tag">{esc(t)}</span>' if t else '')
                        + f'<p>{md(d)}</p></li>' for n, t, d in groups[key])
        blocks.append(f'<section class="group" id="skills-{key}">{head}<ul>{items}</ul></section>')
    names = ('<li><code>/name</code><span>you type it</span></li>'
             '<li><code>name</code><span>Claude loads it when it fits; you can type it too</span></li>'
             '<li><span class="tag">tag</span><span>when it is used</span></li>')

    first_lead = r['lead'][0]
    summary = f'{LEDE} {start} tells you which command comes next; you approve every gate.'
    preload = '\n'.join(f'<link rel="preload" href="fonts/{file}" as="font" type="font/woff2" crossorigin>'
                        for _, file, _ in FACES)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(TITLE)}</title>
<meta name="description" content="{esc(summary)}">
<link rel="canonical" href="{PAGE_URL}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(TITLE)}">
<meta property="og:description" content="{esc(summary)}">
<meta property="og:url" content="{PAGE_URL}">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="{LIGHT['paper']}" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="{DARK['paper']}" media="(prefers-color-scheme: dark)">
<link rel="icon" href="{ICON}">
{preload}
<style>{page_css()}</style>
</head>
<body>
<main class="wrap">
<header>
<h1>{esc(TITLE)}</h1>
<p class="lede">{esc(LEDE)} <code>{esc(start)}</code> tells you which command comes next; you approve every gate.</p>
<ul class="legend" aria-label="Legend">{legend}</ul>
</header>
<section class="box router" aria-label="The router">
<div><p class="kicker">Start here, at any step</p><p class="cmd">{esc(start)}</p><p class="sub">{md(r['never'])}</p></div>
<ol class="beats">{beats}</ol>
</section>
<section class="fork" aria-label="Size of the request">{fork}</section>
<section class="band" aria-label="Once per project">
<h2 class="kicker">Once per project</h2>
{flow_html(r, r['project'])}
</section>
<div class="into-epic" aria-hidden="true">↓</div>
<section class="frame" aria-label="Per epic">
<h2 class="kicker">Per epic · about {r['epics']} per roadmap, never more than {r['most']}</h2>
{flow_html(r, r['lead'], 'flow flow-rev')}
<div class="joint" aria-hidden="true"><span>↓</span><span class="up">↑ Next epic</span></div>
<div class="joint phone" aria-hidden="true"><span>↓</span></div>
<div class="ticket-row">
<section class="ticket" aria-label="Per ticket"><h3 class="kicker">Per ticket</h3>
{flow_html(r, r['ticket'], level=4)}
<p class="loop-note">Changes requested at {r['review']} go back to {r['ticket'][0]}</p>
</section>
{ARR}
{card_html(steps[r['close']])}
</div>
<p class="epic-note">After {r['close']}, the next epic starts again at {first_lead}.</p>
</section>
<section class="panels">
<div><h2>Other ways in</h2><ul>{ways}</ul></div>
<div><h2>Any time</h2><ul>{any_time}</ul></div>
<div><h2>Sessions and gates</h2><ul class="rules">{rules}</ul></div>
</section>
<section class="skills" id="skills">
<h2>Every skill, step by step</h2>
<ul class="legend">{names}</ul>
<div class="groups">{''.join(blocks)}</div>
<p class="foot">Built by <a href="{REPO_URL}/blob/main/docs/build-workflow.py"><code>docs/build-workflow.py</code></a> from <code>skills/ask-team/SKILL.md</code> and <code>skills/ask-team/REGISTRY.md</code> · sources {digest}</p>
</section>
</main>
</body>
</html>
"""


def main():
    args = sys.argv[1:]
    try:
        router = read_router(SKILL)
        groups = read_registry(REGISTRY, router['steps'])
        for _, file, _ in FACES:
            need(os.path.isfile(os.path.join(FONTS, file)), f'docs/fonts has no {file}')
    except SourceError as e:
        print(f'workflow page: cannot read the sources: {e}')
        return 1
    if '--check' in args:
        return 0
    out = args[args.index('--out') + 1] if '--out' in args else PREVIEW
    digest = hashlib.sha256(open(SKILL, 'rb').read() + open(REGISTRY, 'rb').read()).hexdigest()[:10]
    out_dir = os.path.dirname(os.path.abspath(out))
    os.makedirs(out_dir, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(build(router, groups, digest))
    if out_dir != os.path.dirname(FONTS):
        shutil.copytree(FONTS, os.path.join(out_dir, 'fonts'), dirs_exist_ok=True)
    print(f'wrote {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
