#!/usr/bin/env python3
"""Build the team workflow page, the whole workflow on one HTML page.

What the page says about the workflow comes from skills/ask-team/SKILL.md (the
steps, how the router sizes a request, the ways in, the any-time skills, the
session and gate rules) and skills/ask-team/REGISTRY.md (every skill, where it
is used, what it does). SKILL.md speaks to Claude about "the user"; the page
turns that into "you". Only the page's own frame lives here: the title, the
lede and the short glossary. Change those two files, never
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
# Terms the sources use without explaining them; each shows only while a source uses it.
TERMS = [
    ('ADR', r'\bADRs?\b', 'Architecture decision record: a short file that keeps one decision and why it was made.'),
    ('PRD', r'\bPRD\b', 'Product requirements document: what to build, for whom, and how success is measured.'),
    ('Epic', r'\bepic\b', 'One release slice of the roadmap, carried through every per-epic step.'),
    ('Spike', r'\bspike\b', 'One question answered with a throwaway prototype or a write-up, not production code.'),
    ('Fog', r'\bFog\b', 'The way forward is unclear: /wayfinder maps the open decisions before the work starts.'),
    ('Tracer-bullet ticket', r'tracer-bullet', 'A thin slice that runs end to end through every layer, so it can be built and merged on its own.'),
    ('Blocking edge', r'blocking edges?', 'A link saying one ticket has to be done before another can start.'),
    ('CI green', r'\bCI green\b', 'Every automated check on the pull request passes.'),
]

# The router's Sessions section names these roles; the steps it leaves out are yours.
ROLE_WORDS = {'product': 'product', 'tech lead': 'lead', 'developer': 'dev', 'reviewer': 'review'}
ROLE_NAMES = {'product': 'Product', 'lead': 'Tech lead', 'dev': 'Developer',
              'review': 'Reviewer', 'you': 'You'}
GROUP_TITLES = {'start': 'Start here', 'in': 'Other ways in', 'any': 'Any time',
                'other': 'Outside the flow'}

LIGHT = dict(paper='#F2F4F7', surface='#FFFFFF', ink='#16202C', muted='#5B6778',
             rule='#D3DAE2', product='#94600F', lead='#0E7A70', dev='#2C5BC8',
             review='#7445C2', you='#C02E48', on_role='#FFFFFF')
DARK = dict(paper='#18191B', surface='#212225', ink='#E8E9EB', muted='#A0A4AA',
            rule='#34363A', product='#D6A45E', lead='#64B5A7', dev='#93A9E2',
            review='#B7A2E0', you='#E98A93', on_role='#18191B')

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
    answer = [rest for lead, rest in items if lead.lower().startswith('answer')]
    m = re.match(r'with:\s*(.+?)\.(?:\s|$)', answer[0]) if answer else None
    need(m, 'How to route has no "Answer with: ..." item')
    # "the step and why it is next, the exact command ..., and what ..." -> its parts.
    answer = [re.sub(r'\s*\([^)]*\)', '', a).strip() for a in re.split(r',\s*(?:and\s+)?', m.group(1))]
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
        never=never[0], answer=answer, beats=[lead.rstrip('.') for lead, _ in items], fork=fork,
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

    groups, kinds = {}, {}
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
        kinds[name] = row.get('visibility', '')
    need('start' in groups, 'REGISTRY.md has no "entry point" skill')
    return groups, kinds


# ---- Drawing ------------------------------------------------------------------

# SKILL.md speaks to Claude about "the user"; the page speaks to that user.
VOICE = [
    (r'never treat a step as approved because its output exists',
     lambda m: 'a step is approved when you approve it, not when its output exists'),
    (r'\bPast that, propose a split', lambda m: 'Past that, Claude proposes a split'),
    (r"\b([Tt])he user's(?=[:.,;)]|$)", lambda m: m.group(1).replace('t', 'y').replace('T', 'Y') + 'ours'),
    (r"\b([Tt])he user's\b", lambda m: m.group(1).replace('t', 'y').replace('T', 'Y') + 'our'),
    (r'\b([Tt])he user (\w+?)s\b', lambda m: m.group(1).replace('t', 'y').replace('T', 'Y') + 'ou ' + m.group(2)),
    (r'\b([Tt])he user\b', lambda m: m.group(1).replace('t', 'y').replace('T', 'Y') + 'ou'),
]


def voice(s):
    for pattern, repl in VOICE:
        s = re.sub(pattern, repl, s)
    return s


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
            t = esc(voice(seg))
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


AI = '<i class="ai"></i>'
ARR = f'<span class="arr" aria-hidden="true">{AI}</span>'


def card_html(s, level=3):
    label = ROLE_NAMES[s['role']] + (f' · {s["qual"]}' if s['qual'] else '')
    note = f'<p class="note">{md(cap(s["note"]))}</p>' if s['note'] else ''
    out = shown_output(s['output'])
    result = (f'<p class="out">{md(out)}</p>' if out else '') + (
        '<p class="gate-mark"><span class="dia"></span>You approve</p>' if s['gate'] else '')
    return (f'<article class="card{" optional" if s["optional"] else ""} p-{s["role"]}" id="step-{s["n"]}">'
            f'<div class="card-head"><span class="num">{s["n"]}</span>'
            f'<span class="role">{esc(label)}</span></div>'
            f'<h{level} class="title"><a href="#skills-{s["n"]}">{esc(s["name"])}'
            f'<span class="vh">, its skills</span></a></h{level}>{note}'
            f'<p class="cmd-text">{md(s["command"])}</p>'
            + (f'<div class="result">{result}</div>' if result else '') + '</article>')


def flow_html(r, numbers, cls='flow', level=3):
    return f'<div class="{cls}">' + ARR.join(card_html(r['steps'][n], level) for n in numbers) + '</div>'


def answer_html(r):
    """What the router's answer holds, as SKILL.md lists it."""
    items = ''.join(f'<li>{md(cap(a))}</li>' for a in r['answer'])
    return f'<div class="answer"><p class="answer-title">Its answer gives you</p><ol>{items}</ol></div>'


def page_css():
    def tokens(p):
        return ' '.join(f"--{k.replace('_', '-')}:{v};" for k, v in p.items())
    faces = ''.join(f'@font-face{{font-family:"{f}";src:url("fonts/{file}") format("woff2");'
                    f'font-weight:{w};font-style:normal;font-display:swap}}\n'
                    for f, file, w in FACES)
    return faces + f"""
/* Layout: a sticky bar on top, then one column of bands. The epic loop is a dashed
   frame whose rows snake, design to tickets leftwards and build to retro rightwards, so
   the retro sits under the first epic step. Below 1100px everything stacks in reading
   order, in one centred column narrow enough to read. */
:root{{ {tokens(LIGHT)}
  --display:"Bricolage Grotesque","Segoe UI",system-ui,sans-serif;
  --body:"Instrument Sans","Segoe UI",system-ui,-apple-system,sans-serif;
  --mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --gap:30px; --bar:56px;
  --link:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 12' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M1.5 6h28M25 1.8l4.5 4.2-4.5 4.2'/%3E%3C/svg%3E");
  --arrow:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 12h15M13 5.5l6.5 6.5-6.5 6.5'/%3E%3C/svg%3E"); }}
@media (prefers-color-scheme: dark){{ :root{{ {tokens(DARK)} color-scheme:dark; }} }}
*,*::before,*::after{{box-sizing:border-box}}
html{{scroll-padding-top:calc(var(--bar) + 16px)}}
body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--body);font-size:1rem;line-height:1.55}}
.wrap,.bar-in{{max-width:1300px;margin:0 auto;padding-inline:clamp(16px,4vw,40px)}}
.wrap{{padding-block:40px 56px;display:grid;gap:28px}}
.wrap > *,.section > *,.panels > *{{min-width:0}}
h1,h2,h3,h4{{font-family:var(--display);text-wrap:balance;margin:0;line-height:1.15}}
h1{{font-size:clamp(2rem,5vw,3rem);font-weight:700;letter-spacing:-.015em}}
.lede{{color:var(--muted);font-size:1.125rem;max-width:60ch;margin:12px 0 0}}
.lede code{{color:var(--ink)}}
code{{font-family:var(--mono);font-size:.84em;font-weight:600;white-space:nowrap}}
a{{color:inherit;text-underline-offset:.2em}}
::selection{{background:var(--dev);color:var(--on-role)}}
:focus-visible{{outline:2px solid var(--dev);outline-offset:2px;border-radius:3px}}
.vh{{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}}
.skip{{position:absolute;left:16px;top:-60px;z-index:10;background:var(--ink);color:var(--paper);padding:8px 12px;border-radius:6px;font-weight:700}}
.skip:focus{{top:12px}}
.bar{{position:sticky;top:0;z-index:5;background:var(--surface);border-bottom:1px solid var(--rule);box-shadow:0 8px 20px -16px rgb(0 0 0 / .35)}}
.bar ul{{display:flex;align-items:center;gap:4px;list-style:none;margin:0;padding:0;min-height:var(--bar);font-size:.9375rem;font-weight:600}}
.bar a{{display:flex;align-items:center;gap:6px;text-decoration:none;color:var(--muted);padding:7px 12px;border-radius:7px;white-space:nowrap}}
.bar a:hover{{color:var(--ink);background:var(--paper)}}
.bar a{{position:relative}}
.bar a[aria-current]{{color:var(--ink);background:none}}
.bar a[aria-current]::after{{content:"";position:absolute;left:12px;right:12px;bottom:-10px;height:2px;background:var(--ink)}}
.bar .home{{margin-right:8px}}
.bar .home a{{font-family:var(--display);font-size:1.0625rem;font-weight:700;color:var(--ink);padding-left:0}}
.bar .home a:hover{{background:none}}
.bar:not(.scrolled) .home{{display:none}}
.bar:not(.scrolled) li:nth-child(2) a{{margin-left:-12px}}
.bar .out-link{{margin-left:auto}}
.bar .out-link a{{color:var(--ink);border:1px solid var(--rule)}}
.ai{{display:inline-block;flex:none;width:24px;height:24px;background:currentColor;-webkit-mask:var(--arrow) center/contain no-repeat;mask:var(--arrow) center/contain no-repeat}}
.ai.ext{{width:15px;height:15px;transform:rotate(-45deg)}}
/* Between steps, a thin connector rather than a heavy arrow. */
.arr .ai,.joint .ai,.into-epic .ai{{width:26px;height:10px;-webkit-mask-image:var(--link);mask-image:var(--link)}}
.legend{{display:flex;flex-wrap:wrap;gap:8px 20px;list-style:none;padding:0;margin:18px 0 0;font-size:.875rem}}
.legend li{{display:flex;align-items:center;gap:7px}}
.sw{{width:11px;height:11px;border-radius:3px;background:var(--c)}}
.dia{{width:9px;height:9px;background:var(--you);transform:rotate(45deg);flex:none;display:inline-block}}
.dash-sw{{width:22px;height:12px;border:1.5px dashed var(--muted);border-radius:3px}}
.kicker{{font-family:var(--body);line-height:1.5;font-size:.75rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin:0}}
.box{{background:var(--surface);border:1px solid var(--rule);border-radius:12px}}
.router{{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,6fr);gap:20px 32px;padding:22px 24px;align-items:center}}
.router .cmd{{font-family:var(--mono);font-size:1.875rem;font-weight:700;margin:0 0 6px}}
.router .sub{{color:var(--muted);margin:0;font-size:.9375rem;max-width:44ch}}
.router .sub strong{{color:var(--ink)}}
.beats{{display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px;list-style:none;margin:12px 0 0;padding:0;font-size:.875rem;font-weight:700}}
.beats .arr{{flex:none;padding:0;color:var(--muted)}}
.beats .ai{{width:16px;height:16px}}
.answer{{background:var(--paper);border-radius:8px;padding:14px 18px}}
.answer-title{{margin:0 0 8px;font-size:.875rem;font-weight:700;color:var(--muted)}}
.answer ol{{margin:0;padding-left:1.4em;display:grid;gap:4px;font-size:.9375rem}}
.answer li::marker{{color:var(--muted);font-weight:700}}
.fork{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}}
.fork .box{{padding:16px 18px;display:grid;gap:6px;align-content:start}}
.fork h2{{font-size:1.5rem}}
.fork p{{margin:0;font-size:.9375rem}}
.fork em{{font-style:normal;font-weight:700}}
.fork-note{{grid-column:1/-1;color:var(--muted);font-size:.875rem;margin:-8px 0 0}}
.band{{display:grid;gap:12px}}
.flow{{display:flex;align-items:stretch}}
.arr{{flex:0 0 var(--gap);display:flex;justify-content:center;align-items:center;color:var(--muted)}}
.card{{flex:1 1 0;min-width:0;background:var(--surface);border:1px solid var(--rule);border-radius:10px;padding:14px 13px;display:flex;flex-direction:column;gap:8px}}
.card.optional{{border-style:dashed;border-color:var(--muted)}}
.card:target{{box-shadow:0 0 0 2px var(--c),0 6px 18px -8px var(--c)}}
.card-head{{display:flex;align-items:center;gap:9px}}
.num{{width:26px;height:26px;border-radius:6px;background:var(--c);color:var(--on-role);display:grid;place-items:center;font-weight:700;font-size:.8125rem;flex:none;font-variant-numeric:tabular-nums;font-family:var(--body)}}
.role{{font-size:.7188rem;line-height:1.3;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--c);font-family:var(--body)}}
.card .title{{font-size:1.125rem;font-weight:700}}
.card .title a{{text-decoration:underline dotted var(--muted) 1.5px;text-underline-offset:.22em}}
.card .title a:hover{{text-decoration:underline solid var(--c) 2px}}
.note{{margin:-4px 0 0;color:var(--muted);font-size:.8125rem;line-height:1.4}}
.cmd-text{{margin:0;font-size:.8438rem;line-height:1.5}}
.cmd-text code{{font-size:.7812rem;white-space:normal}}
.result{{margin-top:auto;padding-top:9px;border-top:1px solid var(--rule);display:grid;gap:8px}}
.out{{margin:0;font-weight:600;font-size:.8438rem;line-height:1.4}}
.out::before{{content:"→ ";color:var(--muted)}}
.gate-mark{{margin:0;display:flex;align-items:center;gap:8px;color:var(--you);font-weight:700;font-size:.8125rem}}
.frame{{border:1.5px dashed var(--muted);border-radius:16px;padding:26px 20px 18px;position:relative;display:grid}}
.frame > .kicker{{position:absolute;top:-10px;left:16px;background:var(--paper);padding:0 7px}}
.cols4{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));column-gap:var(--gap)}}
.joint{{padding:8px 0;color:var(--muted);font-weight:700}}
.joint span{{display:flex;justify-content:center;align-items:center;gap:4px;min-height:30px}}
.joint .down{{grid-column:1 / span 2;justify-content:flex-start;padding-left:14px;font-size:.875rem}}
.joint .down .ai{{transform:rotate(90deg)}}
.into-epic{{margin:-14px 0;padding-inline:21.5px;color:var(--muted);font-weight:700}}
.into-epic span{{grid-column:1;justify-self:start;display:grid;justify-items:center;gap:2px;font-size:.875rem;line-height:1.3}}
.into-epic .ai{{transform:rotate(90deg);margin:8px 0}}
.ticket-row{{display:flex;align-items:stretch}}
.ticket-row > .card{{flex:1 1 0}}
.ticket{{flex:3 1 0;min-width:0;border:1.5px dashed var(--muted);border-radius:12px;padding:20px 12px 12px;position:relative}}
.ticket > .kicker{{position:absolute;top:-10px;left:14px;background:var(--paper);padding:0 7px}}
.loop-note,.epic-note{{margin:10px 0 0;font-size:.875rem;font-weight:700;display:flex;flex-wrap:wrap;gap:4px 6px;align-items:center}}
.loop-note::before,.epic-note::before{{content:"↺";color:var(--muted);font-size:1.0625rem}}
.epic-note{{margin-top:16px}}
.epic-note span{{font-weight:400;color:var(--muted)}}
.panels{{display:grid;grid-template-columns:repeat(var(--n,3),minmax(0,1fr));gap:24px 40px}}
.panels h2,.panels h3{{font-size:1.5rem;margin-bottom:14px}}
.panels ul,.panels dl{{list-style:none;margin:0;padding:0;display:grid;gap:14px}}
.panels li p{{margin:0}}
.panels .when{{color:var(--muted);font-size:.9375rem}}
.panels dt{{font-weight:700}}
.panels dd{{margin:2px 0 0;color:var(--muted);font-size:.9375rem}}
.rules li{{display:grid;grid-template-columns:16px minmax(0,1fr);gap:6px;align-items:start}}
.rules .dot{{width:7px;height:2px;background:var(--muted);margin-top:12px}}
.rules .dia{{margin-top:8px}}
.section{{border-top:1px solid var(--rule);padding-top:36px;display:grid;gap:14px}}
.section > h2{{font-size:clamp(1.75rem,3.4vw,2.125rem)}}
.phase{{border-top:1px solid var(--rule);padding-top:18px}}
.phase-title{{font-size:1.25rem;margin-bottom:6px}}
/* Three columns in reading order. The script sets each block's row span from its
   height, so a long block leaves no gap under a short one; Tab still follows the steps. */
.groups{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));column-gap:40px;align-items:start;margin-top:10px}}
.groups.packed{{grid-auto-rows:4px}}
.tag.step-tag{{background:var(--c);border-color:var(--c);color:var(--on-role)}}
.group-by{{display:flex;flex-wrap:wrap;align-items:center;gap:10px 14px;border:0;padding:0;margin:8px 0 4px}}
.group-by legend{{float:left;font-weight:700;font-size:1rem}}
.group-by .seg{{display:inline-flex;border:1px solid var(--rule);border-radius:8px;background:var(--surface);overflow:hidden}}
.group-by label{{position:relative;cursor:pointer;padding:7px 16px;font-weight:600;font-size:.9375rem;color:var(--muted)}}
.group-by label + label{{border-left:1px solid var(--rule)}}
.group-by input{{position:absolute;opacity:0;inset:0;margin:0;cursor:pointer}}
.group-by label:hover{{color:var(--ink)}}
.group-by label:has(:checked){{color:var(--ink);font-weight:700;box-shadow:inset 0 -3px 0 var(--ink)}}
.group-by label:has(:focus-visible){{outline:2px solid var(--dev);outline-offset:-4px}}
.group{{break-inside:avoid;margin:0 0 24px;padding:10px 12px;margin-inline:-12px;border-radius:10px}}
.group:target{{background:var(--surface);box-shadow:0 0 0 2px var(--c,var(--rule))}}
.group-head{{display:flex;align-items:baseline;gap:9px;margin-bottom:10px}}
.group h4{{font-size:1.25rem;display:flex;flex-wrap:wrap;align-items:center;gap:4px 9px}}
.group h4 .role{{flex-basis:100%;order:3}}
.group .num{{width:24px;height:24px;font-size:.75rem;border-radius:5px}}
.back{{display:inline-flex;align-items:center;gap:6px;margin-top:12px;font-size:.875rem;font-weight:600;color:var(--muted);text-decoration:none}}
.back .ai{{width:16px;height:16px;transform:rotate(-90deg)}}
.back:hover{{color:var(--ink);text-decoration:underline;text-underline-offset:.2em}}
.group ul{{list-style:none;margin:0;padding:0;display:grid;gap:10px}}
.group li{{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 8px}}
.group li p{{flex-basis:100%;margin:0;color:var(--muted);font-size:.9375rem;line-height:1.45}}
.group li > code{{font-size:.8438rem}}
.group details{{margin-top:10px}}
.group summary{{cursor:pointer;color:var(--muted);font-size:.9375rem;font-weight:600}}
.group summary code{{color:var(--ink)}}
.group summary:hover{{color:var(--ink)}}
.group details ul{{margin-top:10px;padding-left:14px;border-left:1px solid var(--rule)}}
.tag{{display:inline-block;padding:1px 6px;border-radius:4px;background:var(--surface);border:1px solid var(--rule);color:var(--muted);font-size:.7188rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase}}
.foot{{color:var(--muted);font-size:.875rem;margin:8px 0 0;padding-top:20px;border-top:1px solid var(--rule)}}
.foot code{{font-size:.8125rem;white-space:normal}}
.p-product{{--c:var(--product)}} .p-lead{{--c:var(--lead)}} .p-dev{{--c:var(--dev)}} .p-review{{--c:var(--review)}} .p-you{{--c:var(--you)}}
@media (max-width: 1100px){{
  .wrap,.bar-in{{max-width:calc(720px + 2 * clamp(16px,4vw,40px))}}
  .flow,.ticket-row{{flex-direction:column}}
  .flow > .arr,.ticket-row > .arr{{height:34px;flex-basis:auto}}
  .flow > .arr .ai,.ticket-row > .arr .ai{{transform:rotate(90deg)}}
  .joint{{display:none}}
  .joint.phone{{display:flex;justify-content:center}}
  .into-epic{{grid-template-columns:minmax(0,1fr);margin:-18px 0}}
  .into-epic span{{grid-column:1}}
  .ticket{{margin:12px 0 0}}
  .router,.fork,.panels{{grid-template-columns:minmax(0,1fr)}}
  .groups{{grid-template-columns:minmax(0,1fr)}}
  .fork-note{{margin:0}}
  .bar .home a{{font-size:.9375rem}}
  .cmd-text code{{white-space:nowrap}}
}}
/* Side by side, a role label may wrap to two lines: every head keeps room for two,
   so the titles of a row line up. */
@media (min-width: 1101px){{ .joint.phone{{display:none}} .card-head{{min-height:1.875rem}} }}
@media (max-width: 600px){{ .bar .home{{display:none}} .bar li:nth-child(2) a{{margin-left:-12px}} .bar ul{{gap:0}} }}
@media (prefers-reduced-motion: no-preference){{ html{{scroll-behavior:smooth}} }}
"""


BAR_JS = """const bar = document.querySelector('.bar');
const links = [...bar.querySelectorAll('a[href^="#"]:not([href="#top"])')];
const targets = links.map(a => document.querySelector(a.getAttribute('href')));
function mark() {
  bar.classList.toggle('scrolled', document.querySelector('h1').getBoundingClientRect().bottom < 0);
  // The section in view is the last one whose top has passed under the bar.
  let current = -1;
  targets.forEach((t, i) => { if (t.getBoundingClientRect().top < 140) current = i; });
  links.forEach((a, i) => i === current ? a.setAttribute('aria-current', 'location') : a.removeAttribute('aria-current'));
}
addEventListener('scroll', mark, {passive: true});
mark();

// Skills: group them by role (the default), moment, step or kind, and pack the columns.
const byStep = document.getElementById('by-step'), byKind = document.getElementById('by-kind');
const blocks = [...byStep.querySelectorAll('section.group')];
const switcher = document.querySelector('.group-by');
function pack() {
  // Block i goes to column i mod n, straight under the previous block there: rows read
  // left to right in step order, and no column waits for a taller neighbour.
  document.querySelectorAll('.groups').forEach(g => {
    g.classList.remove('packed');
    [...g.children].forEach(c => c.style.gridArea = '');
    const n = getComputedStyle(g).gridTemplateColumns.split(' ').length;
    const items = [...g.children].map(c => [c, c.getBoundingClientRect().height + parseFloat(getComputedStyle(c).marginBottom)]);
    if (n < 2) return;
    g.classList.add('packed');
    const next = Array(n).fill(1);
    items.forEach(([c, h], i) => {
      const col = i % n, span = Math.ceil(h / 4);
      c.style.gridArea = `${next[col]} / ${col + 1} / span ${span}`;
      next[col] += span;
    });
  });
}
function group(by) {
  byKind.hidden = by !== 'kind';
  byStep.hidden = by === 'kind';
  if (by !== 'kind') {
    const names = [...new Set(blocks.map(b => b.dataset[by]))];
    byStep.replaceChildren(...names.map(name => {
      const phase = document.createElement('div'), list = document.createElement('div');
      phase.className = 'phase'; list.className = 'groups';
      const h = document.createElement('h3');
      h.className = 'phase-title'; h.textContent = name;
      phase.append(h);
      list.append(...blocks.filter(b => b.dataset[by] === name));
      phase.append(list);
      return phase;
    }));
  }
  try { localStorage.setItem('group-by', by); } catch (e) {}
  pack();
}
switcher.hidden = false;
switcher.addEventListener('change', e => group(e.target.value));
let saved = 'role';
try { saved = localStorage.getItem('group-by') || 'role'; } catch (e) {}
const choice = switcher.querySelector(`input[value="${saved}"]`);
if (choice) { choice.checked = true; group(saved); } else pack();
addEventListener('resize', pack);
document.fonts.ready.then(pack);
document.addEventListener('toggle', pack, true);"""


def build(router, groups, kinds, digest):
    r = router
    steps = r['steps']
    start = groups['start'][0][0]
    legend = ''.join(f'<li class="p-{k}"><span class="sw"></span>{esc(v)}</li>'
                     for k, v in ROLE_NAMES.items())
    legend += ('<li><span class="dia"></span>Your approval</li>'
               '<li><span class="dash-sw"></span>Only when needed</li>')
    beats = f'<li class="arr" aria-hidden="true">{AI}</li>'.join(f'<li>{esc(b)}</li>' for b in r['beats'])

    # Name the steps the ticket path stands for.
    by_name = {s['name'].lower(): n for n, s in steps.items()}
    path = ('write the ticket, then build it',
            f'write the ticket (step {by_name.get("tickets")}), then build it (step {by_name.get("build")})')
    fork = ''.join(f'<div class="box"><h2>{esc(k)}</h2>'
                   f'<p>{md(s.replace(*path) if "tickets" in by_name and "build" in by_name else s)}</p></div>'
                   for k, s in r['fork'])
    fork += ''.join(f'<p class="fork-note">{md(s)}</p>' for s in r['fork_notes'])

    # The router's ways in and any-time skills, plus any registry one it leaves out.
    does = {n.lstrip('/'): d for entries in groups.values() for n, _, d in entries}
    ways_text = ' '.join(r['ways'])
    ways = ''.join(f'<li><p>{md(w)}</p></li>' for w in r['ways'])
    ways += ''.join(f'<li><p><code>{esc(n)}</code></p><p class="when">{md(d)}</p></li>'
                    for n, _, d in groups.get('in', []) if n.lstrip('/') not in ways_text)
    listed = {n.lstrip('/') for n, _ in r['any_time']}
    any_time = ''.join(f'<li><p><code>{esc(n)}</code></p>'
                       f'<p class="when">{md(cap(w or does.get(n.lstrip("/"), "").rstrip(".")))}</p></li>'
                       for n, w in r['any_time'])
    any_time += ''.join(f'<li><p><code>{esc(n)}</code></p><p class="when">{md(d.rstrip("."))}</p></li>'
                        for n, _, d in groups.get('any', []) if n.lstrip('/') not in listed)
    gates = ''.join(f'<li><span class="dia"></span><span>{md(s)}</span></li>' for s in r['gate_rules'])
    sessions = ''.join(f'<li><span class="dot"></span><span>{md(s)}</span></li>' for s in r['session_rules'])
    source_text = open(SKILL, encoding='utf-8').read() + open(REGISTRY, encoding='utf-8').read()
    terms = ''.join(f'<div><dt>{esc(t)}</dt><dd>{esc(d)}</dd></div>' for t, pattern, d in TERMS
                    if re.search(pattern, source_text, re.I))

    # The skill list, step by step. The router box, Other ways in and Any time already
    # show the rest; a skill another one reads folds under its step.
    blocks = []
    for key in sorted(k for k in groups if isinstance(k, int)) + ['other']:
        if key not in groups:
            continue
        if isinstance(key, int):
            s = steps[key]
            role = ROLE_NAMES[s['role']]
            head = (f'<div class="group-head"><h4><span class="num">{key}</span>{esc(s["name"])}'
                    f'<span class="role">{esc(role)}</span></h4></div>')
            back = (f'<a class="back" href="#step-{key}"><i class="ai"></i>'
                    f'Back to step {key}</a>')
            cls = f' p-{s["role"]}'
        else:
            head = f'<div class="group-head"><h4>{esc(GROUP_TITLES[key])}</h4></div>'
            cls, back = '', ''

        def item(n, t, d):
            return (f'<li><code>{esc(n)}</code>' + (f'<span class="tag">{esc(voice(t))}</span>' if t else '')
                    + f'<p>{md(d)}</p></li>')
        # A skill another command loads ("read by /build-ticket", "under the workshop")
        # folds under that command, named in the summary.
        top, users = [], {}
        for n, t, d in groups[key]:
            m = re.match(r'(?:read by|under)\s+([^;]+);?\s*(.*)', t)
            if not m:
                top.append((n, t, d))
                continue
            by = m.group(1).strip()
            if by.startswith('the '):
                by = next((x for x, tt, _ in groups[key] if not re.match(r'(read by|under)\b', tt)), by)
            users.setdefault(by, []).append((n, m.group(2), d))
        folded = ''
        for by, entries in users.items():
            names = [f'<code>{esc(x if x.startswith("/") else "/" + x)}</code>' for x in by.split(', ')]
            who = ', '.join(names[:-1]) + ' and ' + names[-1] if len(names) > 1 else names[0]
            count = f'{len(entries)} skill{"s" if len(entries) > 1 else ""}'
            folded += (f'<details><summary>Loaded by {who} ({count})</summary>'
                       f'<ul>{"".join(item(*e) for e in entries)}</ul></details>')
        items = ''.join(item(*e) for e in top)
        phase = ('Once per project' if key in r['project'] else 'Per epic' if key in r['lead'] or key == r['close']
                 else 'Per ticket' if key in r['ticket'] else GROUP_TITLES['other'])
        role = ROLE_NAMES[steps[key]['role']] if isinstance(key, int) else GROUP_TITLES['other']
        where = f'Step {key}' if isinstance(key, int) else GROUP_TITLES['other']
        tone = steps[key]['role'] if isinstance(key, int) else ''
        blocks.append(dict(role=role, phase=phase, skills=[(n, where, d, tone) for n, _, d in groups[key]],
                           html=f'<section class="group{cls}" id="skills-{key}" data-role="{esc(role)}" '
                                f'data-moment="{esc(phase)}">{head}<ul>{items}</ul>{folded}{back}</section>'))

    def grouped(field):
        return ''.join(f'<div class="phase"><h3 class="phase-title">{esc(g)}</h3><div class="groups">'
                       + ''.join(b['html'] for b in blocks if b[field] == g) + '</div></div>'
                       for g in dict.fromkeys(b[field] for b in blocks))
    # By kind, the same skills sorted by who can start them, each tagged with its step.
    kind_of = {'typed': 'You start it', 'hidden': 'You start it', 'auto': 'Claude may load it',
               'built-in': 'Built into Claude Code'}
    by_kind = {}
    for b in blocks:
        for n, where, d, tone in b['skills']:
            step = f'<span class="tag step-tag p-{tone}">{esc(where)}</span>' if tone else f'<span class="tag">{esc(where)}</span>'
            by_kind.setdefault(kind_of.get(kinds.get(n), 'You start it'), []).append(
                f'<li><code>{esc(n)}</code>{step}<p>{md(d)}</p></li>')
    by_kind = ''.join(f'<section class="group"><div class="group-head"><h4>{esc(k)}</h4></div><ul>{"".join(by_kind[k])}</ul></section>'
                      for k in dict.fromkeys(kind_of.values()) if k in by_kind)
    group_by = ''.join(f'<label><input type="radio" name="group-by" value="{v}"{" checked" if v == "role" else ""}>{t}</label>'
                       for v, t in (('role', 'Role'), ('moment', 'Moment'), ('kind', 'Kind')))
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
<a class="skip" href="#flow">Skip to the flow</a>
<header class="bar"><nav class="bar-in" aria-label="On this page"><ul>
<li class="home"><a href="#top">{esc(TITLE)}</a></li>
<li><a href="#flow">Flow</a></li><li><a href="#rules">Rules</a></li><li><a href="#skills">Skills</a></li>
<li class="out-link"><a href="{REPO_URL}" target="_blank" rel="noopener">GitHub<i class="ai ext"></i><span class="vh"> (opens in a new tab)</span></a></li>
</ul></nav></header>
<main class="wrap" id="top">
<header>
<h1>{esc(TITLE)}</h1>
<p class="lede">{esc(LEDE)} <code>{esc(start)}</code> tells you which command comes next; you approve every gate.</p>
<ul class="legend" aria-label="Legend">{legend}</ul>
</header>
<section class="box router" aria-label="The router">
<div><p class="cmd">{esc(start)}</p><p class="sub">Start here, at any step. {md(r['never'])}</p>
<ol class="beats" aria-label="What it does">{beats}</ol></div>
{answer_html(r)}
</section>
<section class="fork" aria-label="Size of the request">{fork}</section>
<section class="band" id="flow" aria-labelledby="band-project">
<h2 class="kicker" id="band-project">Once per project</h2>
{flow_html(r, r['project'])}
</section>
<div class="into-epic cols4" aria-hidden="true"><span>Each epic starts here{AI}</span></div>
<section class="frame" aria-labelledby="band-epic">
<h2 class="kicker" id="band-epic">Per epic</h2>
{flow_html(r, r['lead'])}
<div class="joint cols4" aria-hidden="true"><span class="down">{AI}Then, for each ticket: {r['ticket'][0]} to {r['ticket'][-1]}</span></div>
<div class="joint phone" aria-hidden="true"><span class="down">{AI}</span></div>
<div class="ticket-row">
<section class="ticket" aria-labelledby="band-ticket"><h3 class="kicker" id="band-ticket">Per ticket</h3>
{flow_html(r, r['ticket'], level=4)}
<p class="loop-note">Changes requested at {r['review']} go back to {r['ticket'][0]}</p>
</section>
{ARR}
{card_html(steps[r['close']])}
</div>
<p class="epic-note"><a href="#step-{first_lead}">After {r['close']}, the next epic starts again at {first_lead}.</a>
<span>About {r['epics']} epics per roadmap, never more than {r['most']}.</span></p>
</section>
<section class="panels" style="--n:2" aria-label="Beside the flow">
<div><h2>Any time</h2><ul>{any_time}</ul></div>
<div><h2>Other ways in</h2><ul>{ways}</ul></div>
</section>
<section class="section" id="rules" aria-labelledby="rules-title">
<h2 id="rules-title">Rules</h2>
<div class="panels">
<div><h3>Gates</h3><ul class="rules">{gates}</ul></div>
<div><h3>Sessions</h3><ul class="rules">{sessions}</ul></div>
<div><h3>Words used here</h3><dl>{terms}</dl></div>
</div>
</section>
<section class="section" id="skills" aria-labelledby="skills-title">
<h2 id="skills-title">Every skill</h2>
<ul class="legend" aria-label="How to read a skill name">{names}</ul>
<fieldset class="group-by" hidden><legend>Group by</legend><span class="seg">{group_by}</span></fieldset>
<div class="grouping" id="by-step">{grouped('role')}</div>
<div class="grouping" id="by-kind" hidden><div class="phase"><div class="groups">{by_kind}</div></div></div>
<p class="foot">This page is built by <a href="{REPO_URL}/blob/main/docs/build-workflow.py"><code>docs/build-workflow.py</code></a> from <code>skills/ask-team/SKILL.md</code> and <code>skills/ask-team/REGISTRY.md</code>, the files the router itself reads. Sources version {digest}.</p>
</section>
</main>
<script>{BAR_JS}</script>
</body>
</html>
"""




def main():
    args = sys.argv[1:]
    try:
        router = read_router(SKILL)
        groups, kinds = read_registry(REGISTRY, router['steps'])
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
        f.write(build(router, groups, kinds, digest))
    if out_dir != os.path.dirname(FONTS):
        shutil.copytree(FONTS, os.path.join(out_dir, 'fonts'), dirs_exist_ok=True)
    print(f'wrote {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
