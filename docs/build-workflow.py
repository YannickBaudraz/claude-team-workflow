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
README = os.path.join(ROOT, 'README.md')
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
                'other': 'Ad hoc'}
OUTSIDE = 'Outside the flow'

LIGHT = dict(paper='#F2F4F7', surface='#FFFFFF', tray='#E7EBF0', ink='#16202C', muted='#5B6778',
             rule='#D3DAE2', product='#94600F', lead='#0E7A70', dev='#2C5BC8',
             review='#7445C2', you='#C02E48', on_role='#FFFFFF')
DARK = dict(paper='#18191B', surface='#212225', tray='#141517', ink='#E8E9EB', muted='#A0A4AA',
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

    groups, kinds, sources = {}, {}, {}
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
        sources[name] = row.get('source', '').strip('`')
    need('start' in groups, 'REGISTRY.md has no "entry point" skill')
    return groups, kinds, sources


def read_install(path):
    """The README's Install section: what it needs, the commands, and what they do.

    Optional on purpose: when the section is missing or reshaped, the page drops the
    install commands and still builds, so rewording the README never fails the check."""
    try:
        text = open(path, encoding='utf-8').read()
    except OSError:
        return None
    m = re.search(r'^## Install\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    code = m and re.search(r'```\w*\n(.*?)```', m.group(1), re.S)
    if not code:
        return None
    prose = [' '.join(p.split()) for p in re.sub(r'```.*?```', '', m.group(1), flags=re.S).split('\n\n')
             if p.strip()]
    return dict(needs=prose[0] if prose else '', commands=code.group(1).strip().splitlines(),
                after=prose[1] if len(prose) > 1 else '')


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
    """Inline markdown to HTML: `code` (a command's arguments muted), **bold**, *italics*."""
    out = []
    for seg in re.split(r'(`[^`]*`)', s):
        if len(seg) > 1 and seg[0] == seg[-1] == '`':
            code = seg[1:-1]
            name, _, args = code.partition(' <') if code.startswith('/') else (code, '', '')
            # The space sits inside the span, so a long command breaks before its arguments.
            args = f'<span class="arg"> &lt;{esc(args)}</span>' if args else ''
            out.append(f'<code>{esc(name)}{args}</code>')
        else:
            t = esc(voice(seg))
            t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
            t = re.sub(r'\*(.+?)\*', r'<em>\1</em>', t)
            out.append(t)
    return ''.join(out)


def cap(s):
    return s[:1].upper() + s[1:]


def shown_output(output):
    """The output without what the gate mark says, and the gate mark's words.

    "Approved.", "reviewed and approved" and "The user merges." move to the mark, which
    reads "You approve", "You approve before publishing" or "You approve, then merge"."""
    keep, when, merge = [], '', False
    for s in sentences(output):
        if re.fullmatch(r'(both )?approved( by the user)?\.?', s, re.I):
            continue
        if re.fullmatch(r'the user merges\.?', s, re.I):
            merge = True
            continue
        m = re.search(r',?\s*(?:reviewed and )?approved(?: (before \w+))?(?=\.?$)', s, re.I)
        if m:
            when = m.group(1) or ''
            s = s[:m.start()] + s[m.end():]
        keep.append(s)
    mark = 'You approve, then merge' if merge else 'You approve' + (f' {when}' if when else '')
    return ' '.join(keep), mark


AI = '<i class="ai"></i>'


def link():
    """A connector between steps. A gate shows on the card before it, not on the arrow."""
    return f'<span class="link">{AI}</span>'


def arr():
    return f'<span class="arr" aria-hidden="true">{link()}</span>'


def card_html(s, level=3):
    label = ROLE_NAMES[s['role']] + (f' · {s["qual"]}' if s['qual'] else '')
    note = f'<p class="note">{md(cap(s["note"]))}</p>' if s['note'] else ''
    out, mark = shown_output(s['output'])
    result = (f'<p class="out">{link_steps(md(out))}</p>' if out else '') + (
        f'<p class="gate-mark"><span class="dia"></span>{esc(mark)}</p>' if s['gate'] else '')
    return (f'<article class="card{" optional" if s["optional"] else ""} p-{s["role"]}" id="step-{s["n"]}">'
            f'<div class="card-head"><span class="num">{s["n"]}</span>'
            f'<span class="role">{esc(label)}</span></div>'
            f'<h{level} class="title"><span class="vh">Step {s["n"]}, {esc(label)}: </span>'
            f'<a href="#skills-{s["n"]}">{esc(s["name"])}'
            f'<span class="vh">, its skills</span><i class="to-skills"></i></a></h{level}>{note}'
            f'<p class="cmd-text">{md(s["command"])}</p>'
            + (f'<p class="repeat"><i class="loop"></i>Repeats for each {esc(s["qual"][4:])}</p>'
               if s['qual'].startswith('per ') and s['qual'] not in ('per epic', 'per ticket') else '')
            + (f'<div class="result">{result}</div>' if result else '') + '</article>')


def flow_html(r, numbers, cls='flow', level=3):
    cards = [card_html(r['steps'][n], level) for n in numbers]
    joins = [arr() for _ in numbers[:-1]]
    return f'<div class="{cls}">' + ''.join(c + j for c, j in zip(cards, joins + [''])) + '</div>'


def link_steps(h):
    """Link "step 9", "steps 6 to 9" and "(10" in running text to the step's card."""
    def one(m):
        lead, n = m.group(1), int(m.group(2))
        if not 1 <= n <= STEP_COUNT:
            return m.group(0)
        if lead == '(':
            return f'(<a class="step-ref" href="#step-{n}">{m.group(0)[1:]}</a>'
        return f'<a class="step-ref" href="#step-{n}">{m.group(0)}</a>'
    parts = re.split(r'(<[^>]+>)', h)
    depth = 0
    for i, part in enumerate(parts):
        if part.startswith('<'):
            depth += 1 if re.match(r'<(a|code)\b', part) else -1 if re.match(r'</(a|code)>', part) else 0
        elif depth == 0:
            parts[i] = re.sub(r'(\b[Ss]teps? |\()(\d{1,2})(?: to \d{1,2})?(?=[\s),.;:])', one, part)
    return ''.join(parts)


STEP_COUNT = 0
TERM_SKIP = re.compile(r'<(a|code|h[1-4]|title|script|style|summary)\b|class="[^"]*\b(role|num|tag|beats|cmd)\b')


def link_terms(h):
    """Link the first use of each glossary term, outside headings, links and code."""
    todo = [(t, re.compile(rf'(?i){p}')) for t, p, _ in TERMS]
    parts = re.split(r'(<[^>]+>)', h)
    stack = []
    for i, part in enumerate(parts):
        if part.startswith('</'):
            if stack:
                stack.pop()
        elif part.startswith('<'):
            if not re.match(r'<(input|br|img|meta|link|!)', part, re.I) and not part.endswith('/>'):
                stack.append(bool(TERM_SKIP.match(part) or TERM_SKIP.search(part)))
        elif part.strip() and not any(stack):
            # Find every term in the original text first, so no link lands inside another.
            hits = sorted((m.start(), m.end(), t, pat) for t, pat in todo for m in [pat.search(part)] if m)
            out, at = [], 0
            for start, end, t, pat in hits:
                if start < at:
                    continue
                out += [part[at:start], f'<a class="term" href="#term-{slug(t)}">{part[start:end]}</a>']
                at = end
                todo.remove((t, pat))
            parts[i] = ''.join(out) + part[at:]
    return ''.join(parts)


def slug(t):
    return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')


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
  --loop:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 12a8 8 0 1 1-2.6-5.9'/%3E%3Cpath d='M20 4.5v4.2h-4.2'/%3E%3C/svg%3E");
  --chev:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9.5l6 6 6-6'/%3E%3C/svg%3E");
  --arrow:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 12h15M13 5.5l6.5 6.5-6.5 6.5'/%3E%3C/svg%3E");
  --sun:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='4'/%3E%3Cpath d='M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4'/%3E%3C/svg%3E");
  --moon:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z'/%3E%3C/svg%3E");
  --system:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='4' width='18' height='12' rx='2'/%3E%3Cpath d='M8 20h8M12 16v4'/%3E%3C/svg%3E"); }}
/* The theme follows the system unless the toggle in the bar pins one (data-theme on html). */
@media (prefers-color-scheme: dark){{ :root:not([data-theme="light"]){{ {tokens(DARK)} color-scheme:dark; }} }}
:root[data-theme="dark"]{{ {tokens(DARK)} color-scheme:dark; }}
:root[data-theme="light"]{{ color-scheme:light; }}
*,*::before,*::after{{box-sizing:border-box}}
html{{scroll-padding-top:calc(var(--bar) + 16px)}}
body{{margin:0;overflow-x:clip;background:var(--paper);color:var(--ink);font-family:var(--body);font-size:1rem;line-height:1.55}}
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
.bar .theme-li{{margin-left:auto}}
.theme{{display:grid;place-items:center;width:36px;height:36px;padding:0;border:0;border-radius:7px;background:none;color:var(--muted);cursor:pointer}}
.theme:hover{{color:var(--ink);background:var(--paper)}}
.theme i{{width:19px;height:19px;background:currentColor;-webkit-mask:var(--system) center/contain no-repeat;mask:var(--system) center/contain no-repeat}}
.theme[data-mode="light"] i{{-webkit-mask-image:var(--sun);mask-image:var(--sun)}}
.theme[data-mode="dark"] i{{-webkit-mask-image:var(--moon);mask-image:var(--moon)}}
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
.band-title{{font-size:1.375rem;font-weight:700;letter-spacing:-.01em}}
.box{{background:var(--surface);border:1px solid var(--rule);border-radius:12px}}
.router{{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,6fr);gap:20px 32px;padding:22px 24px;align-items:center}}
.router .cmd,.install .cmd{{font-family:var(--mono);font-size:1.875rem;font-weight:700;line-height:1.2;margin:0 0 6px}}
.new-here{{margin:14px 0 0;font-size:.9375rem;color:var(--muted)}}
.new-here a{{color:var(--ink);font-weight:600}}
.router .sub{{color:var(--muted);margin:0;font-size:.9375rem;max-width:44ch}}
.router .sub strong{{color:var(--ink)}}
.beats{{display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px;list-style:none;margin:12px 0 0;padding:0;font-size:.875rem;font-weight:700}}
.beats .arr{{flex:none;padding:0;color:var(--muted)}}
.beats .ai{{width:16px;height:16px}}
.answer{{background:var(--paper);border-radius:8px;padding:14px 18px}}
.answer-title{{margin:0 0 8px;font-size:.9375rem;font-weight:700;color:var(--ink)}}
.answer ol{{margin:0;padding-left:1.4em;display:grid;gap:4px;font-size:.9375rem}}
.answer li::marker{{color:var(--muted);font-weight:700}}
/* Sizing comes before the flow but is not the flow: one compact strip, quieter than the bands. */
.fork{{display:grid;grid-template-columns:minmax(0,11rem) minmax(0,1fr);gap:6px 28px;padding:16px 22px;align-items:baseline}}
.fork > h2{{font-family:var(--body);font-size:1rem;font-weight:700}}
.fork ul{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px 28px}}
.fork h3{{font-family:var(--body);font-size:.9375rem;font-weight:700;display:inline;margin-right:6px}}
.fork li p{{display:inline;margin:0;font-size:.9375rem;color:var(--muted)}}
.fork em{{font-style:normal;font-weight:700;color:var(--ink)}}
.fork-note{{grid-column:2;color:var(--muted);font-size:.875rem;margin:4px 0 0}}
.band{{display:grid;gap:12px}}
.flow{{display:flex;align-items:stretch}}
.arr{{flex:0 0 var(--gap);display:flex;justify-content:center;align-items:center;color:var(--muted)}}
.card{{flex:1 1 0;min-width:0;background:var(--surface);border:1px solid var(--rule);border-radius:10px;padding:14px 13px;display:flex;flex-direction:column;gap:8px}}
.card.optional{{border-style:dashed;border-color:var(--muted)}}
.card:target{{box-shadow:0 0 0 2px var(--c),0 6px 18px -8px var(--c)}}
.card-head{{display:flex;align-items:center;gap:9px}}
.num{{width:26px;height:26px;border-radius:6px;background:var(--c);color:var(--on-role);display:grid;place-items:center;font-weight:700;font-size:.8125rem;flex:none;font-variant-numeric:tabular-nums;font-family:var(--body)}}
.role{{font-size:.75rem;line-height:1.3;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--c);font-family:var(--body)}}
.card .title{{font-size:1.1875rem;font-weight:700}}
/* The title opens the step's skills: a plain link with a down cue, not the glossary's dotted line. */
.card .title a{{text-decoration:none;display:inline-flex;align-items:center;gap:5px}}
.card .title a:hover{{text-decoration:underline solid var(--c) 2px;text-underline-offset:.22em}}
.to-skills{{display:inline-block;flex:none;width:15px;height:15px;background:var(--muted);-webkit-mask:var(--chev) center/contain no-repeat;mask:var(--chev) center/contain no-repeat}}
.card .title a:hover .to-skills{{background:var(--c)}}
.repeat{{margin:0;display:flex;align-items:center;gap:6px;font-size:.8125rem;font-weight:700;color:var(--c)}}
.repeat .loop{{width:15px;height:15px;background:var(--c)}}
.note{{margin:-4px 0 0;color:var(--muted);font-size:.8125rem;line-height:1.4}}
.cmd-text{{margin:0;font-size:.8438rem;line-height:1.6}}
.cmd-text code{{font-size:.8125rem;white-space:normal;color:var(--ink)}}
.arg{{font-weight:400;color:var(--muted);white-space:normal}}
.result{{margin-top:auto;padding-top:9px;border-top:1px solid var(--rule);display:grid;gap:8px}}
.out{{margin:0;font-weight:600;font-size:.8438rem;line-height:1.4}}
.gate-mark{{margin:0;display:flex;align-items:center;gap:8px;color:var(--you);font-weight:700;font-size:.8125rem}}
.frame{{border:1.5px dashed var(--muted);border-radius:16px;padding:30px 20px 18px;position:relative;display:grid;gap:10px}}
.frame > .band-title,.ticket > .band-title{{position:absolute;top:0;left:14px;transform:translateY(-55%);background:var(--paper);padding:0 8px}}
.link{{display:inline-grid;place-items:center}}
.loop{{display:inline-block;flex:none;width:17px;height:17px;background:var(--muted);-webkit-mask:var(--loop) center/contain no-repeat;mask:var(--loop) center/contain no-repeat}}
.cols4{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));column-gap:var(--gap)}}
.joint{{padding:8px 0;color:var(--muted);font-weight:700}}
.joint > span{{display:flex;justify-content:center;align-items:center;gap:4px;min-height:30px}}
.joint .down{{grid-column:1 / span 2;justify-content:flex-start;padding-left:14px;font-size:.875rem}}
.joint .down .ai{{transform:rotate(90deg)}}
.into-epic .link,.joint .link{{margin-inline:4px}}
.into-epic{{margin:-14px 0;padding-inline:21.5px;color:var(--muted);font-weight:700}}
.into-epic > span{{grid-column:1;justify-self:start;display:grid;justify-items:center;gap:2px;font-size:.875rem;line-height:1.3}}
.into-epic .ai{{transform:rotate(90deg);margin:8px 0}}
.ticket-row{{display:flex;align-items:stretch}}
.ticket-row > .card{{flex:1 1 0;align-self:flex-start}}
.ticket{{flex:3 1 0;min-width:0;border:1.5px dashed var(--muted);border-radius:12px;padding:24px 12px 12px;position:relative}}
.ticket > .band-title{{font-size:1.125rem}}
.loop-note,.epic-note{{margin:10px 0 0;font-size:.875rem;font-weight:700;display:flex;flex-wrap:wrap;gap:4px 6px;align-items:center}}
.epic-note{{margin-top:16px}}
.epic-note span{{font-weight:400;color:var(--muted)}}
.panels{{display:grid;grid-template-columns:repeat(var(--n,3),minmax(0,1fr));gap:24px 40px}}
.panels h2{{font-size:1.375rem;margin-bottom:14px}}
.panels h3{{font-size:1.25rem;margin-bottom:14px}}
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
.phase{{padding-top:30px}}
.phase:first-child{{padding-top:8px}}
.phase-title{{font-size:1.25rem;margin-bottom:12px}}
/* Every skill reads as an index: one row per group, the group on the left and its skills
   on the right. Closed, a row lists its skills by name; open, what each does and where it
   comes from. Without the script every row stays open. */
.groups{{border-bottom:1px solid var(--rule)}}
.grouping .phase:last-child .groups{{border-bottom:0}}
.tag.step-tag{{background:var(--c);border-color:var(--c);color:var(--on-role);text-decoration:none}}
.group-by{{display:flex;flex-wrap:wrap;align-items:center;gap:10px 14px;border:0;padding:0;margin:0}}
.group-by legend{{float:left;font-weight:600;font-size:.875rem;color:var(--muted)}}
.group-by .seg{{display:inline-flex;border:1px solid var(--rule);border-radius:8px;background:var(--surface);overflow:hidden}}
.group-by label{{position:relative;cursor:pointer;padding:4px 12px;font-weight:600;font-size:.875rem;color:var(--muted)}}
.group-by label + label{{border-left:1px solid var(--rule)}}
.group-by input{{position:absolute;opacity:0;inset:0;margin:0;cursor:pointer}}
.group-by label:hover{{color:var(--ink)}}
.group-by label:has(:checked){{color:var(--ink);font-weight:700;box-shadow:inset 0 -3px 0 var(--ink)}}
.group-by label:has(:focus-visible){{outline:2px solid var(--dev);outline-offset:-4px}}
/* The grouping and expand controls stay under the bar while you read the skills. Once stuck
   they join the header as its second row: the nav stays solid, the tools sit on a frosted
   layer that lets the list show through, so they read as part of the content below. The
   layer spans the window; the body clips its overhang so the page never scrolls sideways. */
.skill-tools{{position:sticky;top:var(--bar);z-index:4;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px 20px;padding:6px 0;background:var(--paper);border-bottom:1px solid var(--rule)}}
.skill-tools.stuck{{background:none;border-bottom-color:transparent}}
.skill-tools.stuck::before{{content:"";position:absolute;z-index:-1;top:0;bottom:-1px;left:50%;width:100vw;translate:-50% 0;background:color-mix(in srgb,var(--tray) 70%,transparent);-webkit-backdrop-filter:blur(14px) saturate(1.4);backdrop-filter:blur(14px) saturate(1.4);border-bottom:1px solid var(--rule);box-shadow:0 8px 20px -16px rgb(0 0 0 / .35)}}
.has-stuck-tools .bar{{box-shadow:none}}
.group{{scroll-margin-top:68px}}
/* A plain text button: the nav keeps the only bordered button in the header. */
.all{{font:inherit;font-size:.875rem;font-weight:600;cursor:pointer;color:var(--ink);background:none;border:0;border-radius:6px;padding:5px 10px;margin-right:-10px}}
.all:hover{{background:color-mix(in srgb,var(--ink) 8%,transparent)}}
/* Rows reach 12px past the text on each side, so a highlighted row has room inside its own
   box; the rule between rows stays at the text's width. */
.group{{position:relative;display:grid;grid-template-columns:minmax(0,16rem) minmax(0,1fr);column-gap:32px;align-items:start;padding:12px;margin-inline:-12px;border-radius:10px}}
.group::before{{content:"";position:absolute;top:0;left:12px;right:12px;border-top:1px solid var(--rule)}}
/* Reached from a card, the row lifts onto a surface ringed in its role colour. */
.group:target{{background:var(--surface);box-shadow:inset 0 0 0 2px var(--c,var(--rule))}}
.group:target::before,.group:target + .group::before{{display:none}}
.group-head,.group-body{{min-width:0}}
.group h4{{font-size:1.125rem}}
.group h4,.toggle{{display:flex;flex-wrap:wrap;align-items:center;gap:2px 10px;min-height:28px}}
.group h4 .role{{flex-basis:100%;order:3;padding-left:34px}}
#by-step[data-by="role"] .group h4 .role{{display:none}}
.group .num{{width:24px;height:24px;font-size:.75rem;border-radius:5px}}
/* The script turns each heading into the row's toggle, its chevron first. */
.toggle{{width:100%;padding:0;border:0;border-radius:6px;background:none;font:inherit;color:inherit;text-align:left;cursor:pointer}}
.toggle::before{{content:"";flex:none;width:16px;height:16px;background:var(--muted);-webkit-mask:var(--chev) center/contain no-repeat;mask:var(--chev) center/contain no-repeat;transform:rotate(-90deg)}}
.toggle[aria-expanded="true"]::before{{transform:none}}
.toggle:hover::before{{background:var(--ink)}}
.toggle:hover .name{{text-decoration:underline;text-underline-offset:.2em}}
.toggle .role{{padding-left:60px}}
.group-body > ul{{list-style:none;margin:0;padding:3px 0 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(17rem,1fr));gap:16px 36px;align-items:start}}
.group li.also{{display:none}}
.group.closed .group-body > ul{{display:flex;flex-wrap:wrap;gap:0 22px;padding-top:0}}
.group.closed .group-body > ul > li{{display:block;line-height:28px}}
.group.closed li > :not(code),.group.closed details,.group.closed .back{{display:none}}
.group.closed li.also{{display:block;color:var(--muted);font-size:.875rem;font-weight:600}}
.back{{display:inline-flex;align-items:center;gap:6px;margin-top:2px;padding:10px 0;font-size:.875rem;font-weight:600;color:var(--muted);text-decoration:none}}
.back .ai{{width:16px;height:16px;transform:rotate(-90deg)}}
.back:hover{{color:var(--ink);text-decoration:underline;text-underline-offset:.2em}}
.group li{{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 8px}}
.group li p{{flex-basis:100%;margin:0;color:var(--muted);font-size:.9375rem;line-height:1.45}}
.group li > code{{font-size:.875rem}}
.src{{font-size:.8125rem;color:var(--muted);text-decoration-color:var(--rule);padding:6px 0;margin:-6px 0}}
.group li > .src{{flex-basis:100%}}
a.src:hover{{color:var(--ink);text-decoration-color:currentColor}}
.step-ref{{text-decoration-color:var(--muted)}}
.term{{text-decoration:underline dotted var(--muted) 1.5px}}
.panels dt:target{{color:var(--dev)}}
.any-time{{margin:0;line-height:2}}
.any-time a{{text-decoration-color:var(--rule)}}
.group details{{margin-top:14px}}
.group summary{{cursor:pointer;color:var(--muted);font-size:.9375rem;font-weight:600}}
.group summary code{{color:var(--ink)}}
.group summary:hover{{color:var(--ink)}}
.group details ul{{list-style:none;margin:10px 0 0;padding:0 0 0 14px;border-left:1px solid var(--rule);display:grid;grid-template-columns:repeat(auto-fill,minmax(17rem,1fr));gap:12px 36px;align-items:start}}
.tag{{display:inline-block;padding:1px 6px;border-radius:4px;background:var(--surface);border:1px solid var(--rule);color:var(--muted);font-size:.75rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase}}
.install p:not(.foot){{margin:0;max-width:70ch}}
.install .when{{color:var(--muted)}}
.install .then{{margin-top:12px;font-weight:600}}
pre.shell{{margin:0;background:var(--surface);border:1px solid var(--rule);border-radius:10px;padding:14px 18px;overflow-x:auto;max-width:100%}}
pre.shell code{{font-size:.875rem;white-space:pre;line-height:1.7}}
.foot{{color:var(--muted);font-size:.875rem;margin:24px 0 0;padding-top:20px;border-top:1px solid var(--rule)}}
.foot code{{font-size:.8125rem;white-space:normal}}
.p-product{{--c:var(--product)}} .p-lead{{--c:var(--lead)}} .p-dev{{--c:var(--dev)}} .p-review{{--c:var(--review)}} .p-you{{--c:var(--you)}}
@media (max-width: 1100px){{
  .wrap,.bar-in{{max-width:calc(720px + 2 * clamp(16px,4vw,40px))}}
  .flow,.ticket-row{{flex-direction:column}}
  .flow > .arr,.ticket-row > .arr{{height:34px;flex-basis:auto}}
  .flow > .arr .ai,.ticket-row > .arr .ai{{transform:rotate(90deg)}}
  .joint{{display:none}}
  .joint.phone{{display:flex;justify-content:center}}
  .into-epic{{grid-template-columns:minmax(0,1fr);margin:-12px 0}}
  .into-epic > span{{grid-column:1}}
  .ticket{{margin:12px 0 0}}
  .router,.fork,.fork ul,.panels{{grid-template-columns:minmax(0,1fr)}}
  .group{{grid-template-columns:minmax(0,1fr);row-gap:6px}}
  .group-body{{padding-left:26px}}
  .fork-note{{grid-column:1}}
  .bar .home a{{font-size:.9375rem}}
  .cmd-text code{{white-space:nowrap}}
}}
/* Side by side, a role label may wrap to two lines: every head keeps room for two,
   so the titles of a row line up. */
@media (min-width: 1101px){{ .joint.phone{{display:none}} .card-head{{min-height:1.875rem}} }}
@media (max-width: 420px){{ .cmd-text code{{white-space:normal;overflow-wrap:anywhere}} .bar a{{padding-inline:8px}} .bar li:nth-child(2) a{{margin-left:-8px}} .router .cmd,.install .cmd{{font-size:1.5rem}} }}
@media (max-width: 600px){{ .group-by legend{{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}} .group-by label{{padding:7px 12px}} .bar .home{{display:none}} .bar li:nth-child(2) a{{margin-left:-12px}} .bar ul{{gap:0}} }}
@media (prefers-reduced-motion: no-preference){{ html{{scroll-behavior:smooth}} }}
"""


# Runs in the head, before the page paints: a pinned theme never flashes the system one.
THEME_JS = """(function () {
  let t = null;
  try { t = localStorage.getItem('theme'); } catch (e) {}
  if (t !== 'light' && t !== 'dark') return;
  document.documentElement.dataset.theme = t;
  document.querySelectorAll('meta[name="theme-color"]').forEach(m => m.content = t === 'dark' ? '%s' : '%s');
})();""" % (DARK['paper'], LIGHT['paper'])

BAR_JS = """const bar = document.querySelector('.bar');
const links = [...bar.querySelectorAll('a[href^="#"]:not([href="#top"])')];
const targets = links.map(a => document.querySelector(a.getAttribute('href')));
// Theme: system, light or dark, in that cycle. The head script already applied a pinned one.
const themeBtn = document.querySelector('.theme'), modes = ['system', 'light', 'dark'];
function setTheme(mode) {
  const root = document.documentElement, next = modes[(modes.indexOf(mode) + 1) % 3];
  if (mode === 'system') delete root.dataset.theme; else root.dataset.theme = mode;
  document.querySelectorAll('meta[name="theme-color"]').forEach(m => m.content =
    (mode === 'system' ? m.media.includes('dark') : mode === 'dark') ? '@DARK@' : '@LIGHT@');
  themeBtn.dataset.mode = mode;
  const label = `Theme: ${mode === 'system' ? 'match system' : mode}. Switch to ${next === 'system' ? 'match system' : next}`;
  themeBtn.setAttribute('aria-label', label);
  themeBtn.title = label;
  try { mode === 'system' ? localStorage.removeItem('theme') : localStorage.setItem('theme', mode); } catch (e) {}
}
setTheme(document.documentElement.dataset.theme || 'system');
themeBtn.addEventListener('click', () => setTheme(modes[(modes.indexOf(themeBtn.dataset.mode) + 1) % 3]));
themeBtn.hidden = false;

const tools = document.querySelector('.skill-tools'), rest = document.createElement('div');
tools.before(rest);  // marks where the tools sit when not stuck
function mark() {
  bar.classList.toggle('scrolled', document.querySelector('h1').getBoundingClientRect().bottom < 0);
  // The section in view is the last one whose top has passed under the bar.
  let current = -1;
  targets.forEach((t, i) => { if (t.getBoundingClientRect().top < 140) current = i; });
  links.forEach((a, i) => i === current ? a.setAttribute('aria-current', 'location') : a.removeAttribute('aria-current'));
  // The skill tools join the header only while they sit stuck right under it.
  const top = tools.getBoundingClientRect().top, under = parseFloat(getComputedStyle(tools).top);
  const stuck = Math.abs(top - under) < 1 && rest.getBoundingClientRect().top < under - 1;
  tools.classList.toggle('stuck', stuck);
  document.documentElement.classList.toggle('has-stuck-tools', stuck);
}
addEventListener('scroll', mark, {passive: true});
mark();

// Skills: group them by role (the default), moment or kind.
const byStep = document.getElementById('by-step'), byKind = document.getElementById('by-kind');
const blocks = [...byStep.querySelectorAll('section.group')];
const switcher = document.querySelector('.group-by');
function group(by) {
  byStep.dataset.by = by;
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
}

// Each row opens from its heading; one button opens or closes them all, and a card's
// title opens the row of its step.
const status = document.getElementById('skills-status');
const all = document.querySelector('.all');
const groups = [...document.querySelectorAll('section.group')];
function setOpen(g, open) {
  g.classList.toggle('closed', !open);
  g.querySelector('.toggle').setAttribute('aria-expanded', open);
}
function label() {
  all.textContent = groups.some(g => g.classList.contains('closed')) ? 'Expand all' : 'Collapse all';
}
groups.forEach(g => {
  const h = g.querySelector('h4'), b = document.createElement('button');
  b.type = 'button'; b.className = 'toggle';
  b.append(...h.childNodes);
  h.append(b);
  b.addEventListener('click', () => { setOpen(g, g.classList.contains('closed')); label(); });
  setOpen(g, false);
});
all.hidden = false;
all.addEventListener('click', () => {
  const open = groups.some(g => g.classList.contains('closed'));
  groups.forEach(g => setOpen(g, open));
  label();
  status.textContent = open ? 'Every group expanded.' : 'Every group collapsed.';
});
function openTarget() {
  const t = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if (t && t.matches('section.group')) { setOpen(t, true); label(); }
}
addEventListener('hashchange', openTarget);

switcher.hidden = false;
switcher.addEventListener('change', e => {
  group(e.target.value);
  status.textContent = 'Skills grouped by ' + e.target.parentElement.textContent.trim().toLowerCase() + '.';
});
let saved = 'role';
try { saved = localStorage.getItem('group-by') || 'role'; } catch (e) {}
const choice = switcher.querySelector(`input[value="${saved}"]`);
if (choice) { choice.checked = true; group(saved); }
openTarget();""".replace('@DARK@', DARK['paper']).replace('@LIGHT@', LIGHT['paper'])


def build(router, groups, kinds, sources, install, digest):
    global STEP_COUNT
    r = router
    steps = r['steps']
    STEP_COUNT = len(steps)
    start = groups['start'][0][0]
    legend = ''.join(f'<li class="p-{k}"><span class="sw"></span>{esc(v)}</li>'
                     for k, v in ROLE_NAMES.items())
    legend += ('<li><span class="dia"></span>Gate: you approve before moving on</li>'
               '<li><span class="dash-sw"></span>Only when needed</li>')
    beats = f'<li class="arr" aria-hidden="true">{AI}</li>'.join(f'<li>{esc(b)}</li>' for b in r['beats'])

    # Name the steps the ticket path stands for.
    by_name = {s['name'].lower(): n for n, s in steps.items()}
    path = ('write the ticket, then build it',
            f'write the ticket (step {by_name.get("tickets")}), then build it (step {by_name.get("build")})')
    # Each sentence already names its size in bold; the heading is for screen readers.
    fork = ''.join(f'<li><h3 class="vh">{esc(k)}</h3>'
                   f'<p>{link_steps(md(s.replace(*path) if "tickets" in by_name and "build" in by_name else s))}</p></li>'
                   for k, s in r['fork'])
    fork_note = ''.join(f'<p class="fork-note">{md(s)}</p>' for s in r['fork_notes'])
    sizing = next((b for b in r['beats'] if b.lower().startswith('size')), 'Size the request')

    # The router's ways in and any-time skills, plus any registry one it leaves out.
    ways_text = ' '.join(r['ways'])
    ways = ''.join(f'<li><p>{link_steps(md(w))}</p></li>' for w in r['ways'])
    ways += ''.join(f'<li><p><code>{esc(n)}</code></p><p class="when">{md(d)}</p></li>'
                    for n, _, d in groups.get('in', []) if n.lstrip('/') not in ways_text)
    # Any time: the names only, each linked to the group that describes it, so the page
    # says what a skill does in one place.
    home = {n.lstrip('/'): k for k, entries in groups.items() for n, _, _ in entries}
    listed = [n for n, _ in r['any_time']]
    listed += [n for n, _, _ in groups.get('any', []) if n.lstrip('/') not in {x.lstrip('/') for x in listed}]
    any_time = ', '.join(f'<a href="#skills-{home.get(n.lstrip("/"), "any")}"><code>{esc(n)}</code></a>'
                         for n in listed)
    gates = ''.join(f'<li><span class="dia"></span><span>{link_steps(md(s))}</span></li>' for s in r['gate_rules'])
    sessions = ''.join(f'<li><span class="dot"></span><span>{link_steps(md(s))}</span></li>' for s in r['session_rules'])
    source_text = open(SKILL, encoding='utf-8').read() + open(REGISTRY, encoding='utf-8').read()
    terms = ''.join(f'<div><dt id="term-{slug(t)}">{esc(t)}</dt><dd>{esc(d)}</dd></div>' for t, pattern, d in TERMS
                    if re.search(pattern, source_text, re.I))

    def source(n):
        """Where a skill comes from: its repository, linked, or Claude Code for a built-in."""
        src = sources.get(n, '')
        if re.fullmatch(r'[\w.-]+/[\w.-]+', src):
            return (f'<a class="src" href="https://github.com/{esc(src)}">{esc(src)}'
                    f'<span class="vh"> (source repository)</span></a>')
        return f'<span class="src">{esc(src)}</span>' if src else ''

    # Every skill in the registry, step by step, then the ones outside the flow; a skill
    # another one reads folds under its step.
    blocks = []
    for key in sorted(k for k in groups if isinstance(k, int)) + ['start', 'in', 'any', 'other']:
        if key not in groups:
            continue
        if isinstance(key, int):
            s = steps[key]
            role = ROLE_NAMES[s['role']]
            head = (f'<div class="group-head"><h4><span class="num">{key}</span><span class="name">{esc(s["name"])}</span>'
                    f'<span class="role">{esc(role)}</span></h4></div>')
            back = (f'<a class="back" href="#step-{key}"><i class="ai"></i>'
                    f'Back to step {key}</a>')
            cls = f' p-{s["role"]}'
        else:
            head = f'<div class="group-head"><h4><span class="name">{esc(GROUP_TITLES[key])}</span></h4></div>'
            cls, back = '', ''

        def item(n, t, d):
            t = '' if key == 'start' else t
            return (f'<li><code>{esc(n)}</code>' + (f'<span class="tag">{esc(voice(t))}</span>' if t else '')
                    + f'<p>{md(d)}</p>{source(n)}</li>')
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
        # Closed, a row lists its own skills by name and counts the ones they load.
        loaded = sum(len(e) for e in users.values())
        items += f'<li class="also">+{loaded} more</li>' if loaded else ''
        phase = ('Once per project' if key in r['project'] else 'Per epic' if key in r['lead'] or key == r['close']
                 else 'Per ticket' if key in r['ticket'] else OUTSIDE)
        role = ROLE_NAMES[steps[key]['role']] if isinstance(key, int) else OUTSIDE
        where = f'Step {key}' if isinstance(key, int) else GROUP_TITLES[key]
        tone = steps[key]['role'] if isinstance(key, int) else ''
        blocks.append(dict(role=role, phase=phase, skills=[(n, where, d, tone) for n, _, d in groups[key]],
                           html=f'<section class="group{cls}" id="skills-{key}" data-role="{esc(role)}" '

                                f'data-moment="{esc(phase)}">{head}'
                                f'<div class="group-body"><ul>{items}</ul>{folded}{back}</div></section>'))

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
            step = (f'<a class="tag step-tag p-{tone}" href="#step-{where.split()[-1]}">{esc(where)}</a>' if tone
                    else f'<span class="tag">{esc(where)}</span>')
            by_kind.setdefault(kind_of.get(kinds.get(n), 'You start it'), []).append(
                f'<li><code>{esc(n)}</code>{step}<p>{md(d)}</p>{source(n)}</li>')
    by_kind = ''.join(f'<section class="group"><div class="group-head"><h4><span class="name">{esc(k)}</span></h4></div>'
                      f'<div class="group-body"><ul>{"".join(by_kind[k])}</ul></div></section>'
                      for k in dict.fromkeys(kind_of.values()) if k in by_kind)
    group_by = ''.join(f'<label><input type="radio" name="group-by" value="{v}"{" checked" if v == "role" else ""}>{t}</label>'
                       for v, t in (('role', 'Role'), ('moment', 'Moment'), ('kind', 'Kind')))
    names = ('<li><code>/name</code><span>you type it</span></li>'
             '<li><code>name</code><span>Claude loads it when it fits; you can type it too</span></li>'
             '<li><span class="tag">tag</span><span>when it is used</span></li>')

    if install:
        commands = '\n'.join(esc(c) for c in install['commands'])
        install_html = (f'<p>{md(install["needs"])}</p>' if install['needs'] else '') + (
            f'<pre class="shell"><code>{commands}</code></pre>'
            + (f'<p class="when">{md(install["after"])}</p>' if install['after'] else ''))
    else:
        install_html = f'<p>Install it from <a href="{REPO_URL}">the repository</a>; its README says how.</p>'

    first_lead = r['lead'][0]
    summary = f'{LEDE} {start} tells you which command comes next; you approve every gate.'
    preload = '\n'.join(f'<link rel="preload" href="fonts/{file}" as="font" type="font/woff2" crossorigin>'
                        for _, file, _ in FACES)
    page = f"""<!doctype html>
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
<script>{THEME_JS}</script>
<link rel="icon" href="{ICON}">
{preload}
<style>{page_css()}</style>
</head>
<body>
<a class="skip" href="#top">Skip to content</a>
<header class="bar"><nav class="bar-in" aria-label="On this page"><ul>
<li class="home"><a href="#top">{esc(TITLE)}</a></li>
<li><a href="#flow">Flow</a></li><li><a href="#rules">Rules</a></li><li><a href="#skills">Skills</a></li><li><a href="#install">Install</a></li>
<li class="theme-li"><button type="button" class="theme" hidden><i></i></button></li>
<li class="out-link"><a href="{REPO_URL}" target="_blank" rel="noopener">GitHub<i class="ai ext"></i><span class="vh"> (opens in a new tab)</span></a></li>
</ul></nav></header>
<main class="wrap" id="top">
<header>
<h1>{esc(TITLE)}</h1>
<p class="lede">{esc(LEDE)} <code>{esc(start)}</code> tells you which command comes next; you approve every gate.</p>
</header>
<section class="box router" aria-labelledby="router-title">
<div><h2 class="cmd" id="router-title">{esc(start)}</h2><p class="sub">Start here, at any step. {md(r['never'])}</p>
<ol class="beats" aria-label="What it does">{beats}</ol>
<p class="new-here">New here? <a href="#install">Install it first</a>.</p></div>
{answer_html(r)}
</section>
<section class="box fork" aria-labelledby="fork-title">
<h2 id="fork-title">{esc(sizing)}</h2><ul>{fork}</ul>{fork_note}
</section>
<ul class="legend" aria-label="How to read the flow">{legend}</ul>
<section class="band" id="flow" aria-labelledby="band-project">
<h2 class="band-title" id="band-project">Once per project</h2>
{flow_html(r, r['project'])}
</section>
<div class="into-epic cols4"><span>Each epic starts here{link()}</span></div>
<section class="frame" aria-labelledby="band-epic">
<h2 class="band-title" id="band-epic">Per epic</h2>
{flow_html(r, r['lead'])}
<div class="joint cols4"><span class="down">{link()}Then, for each ticket: steps {r['ticket'][0]} to {r['ticket'][-1]}</span></div>
<div class="joint phone"><span class="down">{link()}Then, for each ticket: steps {r['ticket'][0]} to {r['ticket'][-1]}</span></div>
<div class="ticket-row">
<section class="ticket" aria-labelledby="band-ticket"><h3 class="band-title" id="band-ticket">Per ticket</h3>
{flow_html(r, r['ticket'], level=4)}
<p class="loop-note"><i class="loop"></i>Changes requested at {r['review']} go back to {r['ticket'][0]}</p>
</section>
{arr()}
{card_html(steps[r['close']])}
</div>
<p class="epic-note"><i class="loop"></i><a href="#step-{first_lead}">After {r['close']}, the next epic starts again at {first_lead}.</a></p>
</section>
<section class="panels" style="--n:2" aria-label="Beside the flow">
<div><h2>Other ways in</h2><ul>{ways}</ul></div>
<div><h2>Any time</h2><p class="any-time">{any_time}</p></div>
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
<div class="skill-list">
<div class="skill-tools"><fieldset class="group-by" hidden><legend>Group by</legend><span class="seg">{group_by}</span></fieldset>
<button type="button" class="all" hidden>Expand all</button></div>
<p class="vh" aria-live="polite" id="skills-status"></p>
<div class="grouping" id="by-step" data-by="role">{grouped('role')}</div>
<div class="grouping" id="by-kind" hidden><div class="phase"><div class="groups">{by_kind}</div></div></div>
</div>
</section>
<section class="section install" id="install" aria-labelledby="install-title">
<h2 id="install-title">Run it on your project</h2>
{install_html}
<p class="then">Then, in your project, start Claude Code and run</p>
<p class="cmd">{esc(start)}</p>
<p class="when">It tells you the next command, the session to run it in, and what you approve first.</p>
<p class="foot">This page is built by <a href="{REPO_URL}/blob/main/docs/build-workflow.py"><code>docs/build-workflow.py</code></a> from <code>skills/ask-team/SKILL.md</code> and <code>skills/ask-team/REGISTRY.md</code>, the files the router itself reads. Sources fingerprint {digest}, a hash of both files.</p>
</section>
</main>
<script>{BAR_JS}</script>
</body>
</html>
"""
    # The glossary sits below the flow: link each term the first time the page uses it.
    head, sep, rest = page.partition('<main')
    body, sep2, tail = rest.partition('id="rules"')
    return head + sep + link_terms(body) + sep2 + tail




def main():
    args = sys.argv[1:]
    try:
        router = read_router(SKILL)
        groups, kinds, sources = read_registry(REGISTRY, router['steps'])
        install = read_install(README)
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
        f.write(build(router, groups, kinds, sources, install, digest))
    if out_dir != os.path.dirname(FONTS):
        shutil.copytree(FONTS, os.path.join(out_dir, 'fonts'), dirs_exist_ok=True)
    print(f'wrote {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
