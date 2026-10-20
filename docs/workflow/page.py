"""Assembling the page: the HTML, with its stylesheet and scripts from the files beside this one.

page.css holds /* LIGHT_TOKENS */ and /* DARK_TOKENS */ where Reader's colour variables go,
and /* PALETTES */ where the other palettes go; theme.js and page.js hold @PAPERS@ where
each palette's paper colours go, for the browser's theme-color."""
import json
import os
import re

from . import render
from .config import (DARK, FACES, GROUP_TITLES, ICON, LEDE, LIGHT, OUTSIDE, PAGE_URL, PALETTE_SOURCES,
                     PALETTES, REGISTRY, REPO_URL, ROLE_NAMES, SKILL, TERMS, TITLE)
from .palettes import PAPERS, palette_css, tokens
from .render import (AI, answer_html, answers, arr, card_html, esc, flow_html, link, link_steps, link_terms, md,
                     slug, voice)

HERE = os.path.dirname(os.path.abspath(__file__))
# Links that leave the page open in a new tab, and say so to a screen reader.
NEW_TAB = ' target="_blank" rel="noopener"'
NEW_TAB_NOTE = '<span class="vh"> (opens in a new tab)</span>'


def asset(name):
    """A stylesheet or script beside this file, with the palettes' paper colours filled in."""
    text = open(os.path.join(HERE, name), encoding='utf-8').read().rstrip('\n')
    return text.replace('@PAPERS@', PAPERS)


def page_css():
    faces = ''.join(f'@font-face{{font-family:"{family}";src:url("fonts/{file}") format("woff2");'
                    f'font-weight:{weights};font-style:normal;font-display:swap}}\n'
                    for family, file, weights in FACES)
    css = asset('page.css') + '\n'
    return faces + '\n' + (css.replace('/* LIGHT_TOKENS */', tokens(LIGHT)).replace('/* DARK_TOKENS */', tokens(DARK))
                           .replace('/* PALETTES */', palette_css()))


def appearance_html():
    """The bar's appearance menu: the mode and the palette, in a popover under its button."""
    modes = ''.join(f'<label><input type="radio" name="mode" value="{value}"><i class="mi {value}"></i>{label}</label>'
                    for value, label in (('system', 'System'), ('light', 'Light'), ('dark', 'Dark')))
    palettes = ''.join(f'<label><input type="radio" name="palette" value="{key}">'
                       f'<span class="swatch" data-swatch="{key}" aria-hidden="true"><i></i><i></i><i></i><i></i></span>'
                       f'{esc(name)}</label>' for key, name, _, _ in PALETTES)
    return ('<li class="theme-li"><button type="button" class="theme" popovertarget="appearance" hidden><i></i><b class="chev"></b></button>'
            '<div class="appearance" id="appearance" popover role="group" aria-label="Appearance">'
            f'<fieldset><legend>Mode</legend><span class="seg">{modes}</span></fieldset>'
            f'<fieldset class="palettes"><legend>Palette</legend>{palettes}</fieldset>'
            '</div></li>')


THEME_JS = asset('theme.js')
BAR_JS = asset('page.js')


def build(router, groups, kinds, sources, install, digest, version=None):
    steps = router['steps']
    render.STEP_COUNT = len(steps)
    start = groups['start'][0][0]
    legend = ''.join(f'<li class="p-{role}"><span class="sw"></span>{esc(name)}</li>'
                     for role, name in ROLE_NAMES.items())
    legend += ('<li><span class="dia"></span>Gate: you approve before moving on</li>'
               '<li><span class="dash-sw"></span>Only when needed</li>')
    beats = f'<li class="arr" aria-hidden="true">{AI}</li>'.join(f'<li>{esc(beat)}</li>' for beat in router['beats'])

    # Name the steps the ticket path stands for.
    by_name = {step['name'].lower(): number for number, step in steps.items()}
    path = ('write the ticket, then build it',
            f'write the ticket (step {by_name.get("tickets")}), then build it (step {by_name.get("build")})')
    # Each sentence already names its size in bold; the heading is for screen readers.
    fork = ''.join(f'<li><h3 class="vh">{esc(size)}</h3>'
                   f'<p>{link_steps(md(sentence.replace(*path) if "tickets" in by_name and "build" in by_name else sentence))}</p></li>'
                   for size, sentence in router['fork'])
    fork_note = ''.join(f'<p class="fork-note">{md(note)}</p>' for note in router['fork_notes'])
    sizing = next((beat for beat in router['beats'] if beat.lower().startswith('size')), 'Size the request')

    # The router's ways in and any-time skills, plus any registry one it leaves out.
    ways_text = ' '.join(router['ways'])
    ways = ''.join(f'<li><p>{link_steps(md(way))}</p></li>' for way in router['ways'])
    ways += ''.join(f'<li><p><code>{esc(name)}</code></p><p class="when">{md(does)}</p></li>'
                    for name, _, does in groups.get('in', []) if name.lstrip('/') not in ways_text)
    # Any time: the names only, each linked to the group that describes it, so the page
    # says what a skill does in one place.
    home = {name.lstrip('/'): key for key, entries in groups.items() for name, _, _ in entries}
    listed = [name for name, _ in router['any_time']]
    already = {name.lstrip('/') for name in listed}
    listed += [name for name, _, _ in groups.get('any', []) if name.lstrip('/') not in already]
    any_time = ', '.join(f'<a href="#skills-{home.get(name.lstrip("/"), "any")}"><code>{esc(name)}</code></a>'
                         for name in listed)
    gates = ''.join(f'<li><span class="dia"></span><span>{link_steps(md(rule))}</span></li>'
                    for rule in router['gate_rules'])
    sessions = ''.join(f'<li><span class="dot"></span><span>{link_steps(md(rule))}</span></li>'
                       for rule in router['session_rules'])
    source_text = open(SKILL, encoding='utf-8').read() + open(REGISTRY, encoding='utf-8').read()
    terms = ''.join(f'<div><dt id="term-{slug(term)}">{esc(term)}</dt><dd>{esc(meaning)}</dd></div>'
                    for term, pattern, meaning in TERMS if re.search(pattern, source_text, re.I))

    def source(name):
        """Where a skill comes from: its repository, linked, or Claude Code for a built-in."""
        src = sources.get(name, '')
        if re.fullmatch(r'[\w.-]+/[\w.-]+', src):
            return (f'<a class="src" href="https://github.com/{esc(src)}"{NEW_TAB}>{esc(src)}'
                    f'<span class="vh"> (source repository, opens in a new tab)</span></a>')
        return f'<span class="src">{esc(src)}</span>' if src else ''

    # Every skill in the registry, step by step, then the ones outside the flow; a skill
    # another one reads folds under its step.
    blocks = []
    for key in sorted(key for key in groups if isinstance(key, int)) + ['start', 'in', 'any', 'other']:
        if key not in groups:
            continue
        if isinstance(key, int):
            step = steps[key]
            role = ROLE_NAMES[step['role']]
            head = (f'<div class="group-head"><h4><span class="num">{key}</span><span class="name">{esc(step["name"])}</span>'
                    f'<span class="role">{esc(role)}</span></h4></div>')
            back = (f'<a class="back" href="#step-{key}"><i class="ai"></i>'
                    f'Back to step {key}</a>')
            cls = f' p-{step["role"]}'
        else:
            head = f'<div class="group-head"><h4><span class="name">{esc(GROUP_TITLES[key])}</span></h4></div>'
            cls, back = '', ''

        def item(name, tag, does):
            tag = '' if key == 'start' else tag
            return (f'<li><code>{esc(name)}</code>' + (f'<span class="tag">{esc(voice(tag))}</span>' if tag else '')
                    + f'<p>{md(does)}</p>{source(name)}</li>')
        # A skill another command loads ("read by /build-ticket", "under the workshop")
        # folds under that command, named in the summary.
        top, users = [], {}
        for name, tag, does in groups[key]:
            loaded_by = re.match(r'(?:read by|under)\s+([^;]+);?\s*(.*)', tag)
            if not loaded_by:
                top.append((name, tag, does))
                continue
            by = loaded_by.group(1).strip()
            if by.startswith('the '):
                by = next((other for other, other_tag, _ in groups[key]
                           if not re.match(r'(read by|under)\b', other_tag)), by)
            users.setdefault(by, []).append((name, loaded_by.group(2), does))
        folded = ''
        for by, entries in users.items():
            names = [f'<code>{esc(user if user.startswith("/") else "/" + user)}</code>' for user in by.split(', ')]
            who = ', '.join(names[:-1]) + ' and ' + names[-1] if len(names) > 1 else names[0]
            count = f'{len(entries)} skill{"s" if len(entries) > 1 else ""}'
            folded += (f'<details><summary>Loaded by {who} ({count})</summary>'
                       f'<ul>{"".join(item(*entry) for entry in entries)}</ul></details>')
        items = ''.join(item(*entry) for entry in top)
        # Closed, a row lists its own skills by name and counts the ones they load.
        loaded = sum(len(entries) for entries in users.values())
        items += f'<li class="also">+{loaded} more</li>' if loaded else ''
        phase = ('Once per project' if key in router['project']
                 else 'Per epic' if key in router['lead'] or key == router['close']
                 else 'Per ticket' if key in router['ticket'] else OUTSIDE)
        role = ROLE_NAMES[steps[key]['role']] if isinstance(key, int) else OUTSIDE
        where = f'Step {key}' if isinstance(key, int) else GROUP_TITLES[key]
        tone = steps[key]['role'] if isinstance(key, int) else ''
        blocks.append(dict(role=role, phase=phase, skills=[(name, where, does, tone) for name, _, does in groups[key]],
                           html=f'<section class="group{cls}" id="skills-{key}" data-role="{esc(role)}" '
                                f'data-moment="{esc(phase)}">{head}'
                                f'<div class="group-body"><ul>{items}</ul>{folded}{back}</div></section>'))

    def grouped(field):
        return ''.join(f'<div class="phase"><h3 class="phase-title">{esc(title)}</h3><div class="groups">'
                       + ''.join(block['html'] for block in blocks if block[field] == title) + '</div></div>'
                       for title in dict.fromkeys(block[field] for block in blocks))
    # By kind, the same skills sorted by who can start them, each tagged with its step.
    kind_of = {'typed': 'You start it', 'hidden': 'You start it', 'auto': 'Claude may load it',
               'built-in': 'Built into Claude Code'}
    by_kind = {}
    for block in blocks:
        for name, where, does, tone in block['skills']:
            step_tag = (f'<a class="tag step-tag p-{tone}" href="#step-{where.split()[-1]}">{esc(where)}</a>' if tone
                        else f'<span class="tag">{esc(where)}</span>')
            by_kind.setdefault(kind_of.get(kinds.get(name), 'You start it'), []).append(
                f'<li><code>{esc(name)}</code>{step_tag}<p>{md(does)}</p>{source(name)}</li>')
    by_kind = ''.join(f'<section class="group"><div class="group-head"><h4><span class="name">{esc(kind)}</span></h4></div>'
                      f'<div class="group-body"><ul>{"".join(by_kind[kind])}</ul></div></section>'
                      for kind in dict.fromkeys(kind_of.values()) if kind in by_kind)
    group_by = ''.join(f'<label><input type="radio" name="group-by" value="{value}"{" checked" if value == "role" else ""}>{label}</label>'
                       for value, label in (('role', 'Role'), ('moment', 'Moment'), ('kind', 'Kind')))
    names = ('<li><code>/name</code><span>you type it</span></li>'
             '<li><code>name</code><span>Claude loads it when it fits; you can type it too</span></li>'
             '<li><span class="tag">tag</span><span>when it is used</span></li>')

    if install:
        commands = '\n'.join(esc(command) for command in install['commands'])
        install_html = (f'<p>{md(install["needs"])}</p>' if install['needs'] else '') + (
            f'<pre class="shell"><code>{commands}</code></pre>'
            + (f'<p class="when">{md(install["after"])}</p>' if install['after'] else ''))
    else:
        install_html = f'<p>Install it from <a href="{REPO_URL}"{NEW_TAB}>the repository{NEW_TAB_NOTE}</a>; its README says how.</p>'

    first_lead = router['lead'][0]
    summary = f'{LEDE} {start} tells you which command comes next; you approve every gate.'
    palette_links = [f'<a href="{url}"{NEW_TAB}>{esc(name)}{NEW_TAB_NOTE}</a>' for name, url in PALETTE_SOURCES]
    credits = ', '.join(palette_links[:-1]) + ' and ' + palette_links[-1]
    # The commit the page was built from, linked, and its date.
    built = (f'<p class="version">Version <a href="{REPO_URL}/commit/{version["full"]}"{NEW_TAB}><code>{version["short"]}</code>{NEW_TAB_NOTE}</a>'
             f' · <time datetime="{version["date"]}">{version["date"]}</time>'
             + (' · with local changes' if version['changed'] else '') + '</p>') if version else ''
    # What /ask-team answers at each step, for page.js; a "</" can't end the script early.
    answers_json = json.dumps(answers(router)).replace('</', '<\\/')
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
{appearance_html()}
<li class="out-link"><a href="{REPO_URL}"{NEW_TAB}>GitHub<i class="ai ext"></i>{NEW_TAB_NOTE}</a></li>
</ul></nav></header>
<main class="wrap" id="top">
<header>
<h1>{esc(TITLE)}</h1>
<p class="lede">{esc(LEDE)} <code>{esc(start)}</code> tells you which command comes next; you approve every gate.</p>
{built}
</header>
<section class="box router" aria-labelledby="router-title">
<div><h2 class="cmd" id="router-title">{esc(start)}</h2><p class="sub">Start here, at any step. {md(router['never'])}</p>
<ol class="beats" aria-label="What it does">{beats}</ol>
<p class="new-here">New here? <a href="#install">Install it first</a>.</p></div>
{answer_html(router)}
</section>
<section class="box fork" aria-labelledby="fork-title">
<h2 id="fork-title">{esc(sizing)}</h2><ul>{fork}</ul>{fork_note}
</section>
<ul class="legend" aria-label="How to read the flow">{legend}</ul>
<section class="band" id="flow" aria-labelledby="band-project">
<h2 class="band-title" id="band-project">Once per project</h2>
{flow_html(router, router['project'])}
</section>
<div class="into-epic cols4"><span>{link()}Each epic starts here</span></div>
<section class="frame" aria-labelledby="band-epic">
<h2 class="band-title" id="band-epic">Per epic</h2>
{flow_html(router, router['lead'])}
<div class="joint cols4"><span class="down">{link()}Then, for each ticket: steps {router['ticket'][0]} to {router['ticket'][-1]}</span></div>
<div class="joint phone"><span class="down">{link()}Then, for each ticket: steps {router['ticket'][0]} to {router['ticket'][-1]}</span></div>
<div class="ticket-row">
<section class="ticket" aria-labelledby="band-ticket"><h3 class="band-title" id="band-ticket">Per ticket</h3>
{flow_html(router, router['ticket'], level=4)}
<p class="loop-note"><i class="loop"></i>Changes requested at {router['review']} go back to {router['ticket'][0]}</p>
</section>
{arr()}
{card_html(steps[router['close']])}
</div>
<p class="epic-note"><i class="loop"></i><a href="#step-{first_lead}">After {router['close']}, the next epic starts again at {first_lead}.</a></p>
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
<p class="foot">This page is built by <a href="{REPO_URL}/blob/main/docs/build-workflow.py"{NEW_TAB}><code>docs/build-workflow.py</code>{NEW_TAB_NOTE}</a> from <code>skills/ask-team/SKILL.md</code> and <code>skills/ask-team/REGISTRY.md</code>, the files the router itself reads. Sources fingerprint {digest}, a hash of both files. The {credits} palettes keep their authors' published colours, apart from a few text colours changed to read at 4.5:1 or better, and Tokyo Night Day's blue text set in dark slate.</p>
</section>
</main>
<aside class="dock" id="dock" aria-labelledby="dock-step" aria-keyshortcuts="ArrowRight ArrowLeft Escape" tabindex="-1" hidden><div class="dock-in">
<div class="dock-head"><span class="num"></span><div><p class="dock-step" id="dock-step" aria-live="polite"></p><p class="role dock-role"></p><p class="dock-via"></p><p class="dock-score"></p></div></div>
<dl class="dock-answer"><div class="dock-run"><dt>Run</dt><dd></dd></div><div class="dock-session"><dt>Session</dt><dd></dd></div><div class="dock-gate"><dt>Gate</dt><dd></dd></div></dl>
<div class="dock-play"><div class="dock-next" role="group" aria-label="When this step is done"></div><p class="dock-keys" aria-hidden="true"></p></div>
<button type="button" class="dock-close" aria-label="Close the answer" aria-keyshortcuts="Escape" title="Close (Esc)"><i></i></button>
</div></aside>
<script type="application/json" id="answers">{answers_json}</script>
<a class="to-top" href="#top"><i class="ai"></i><span class="vh">Back to top</span></a>
<script>{BAR_JS}</script>
</body>
</html>
"""
    # The glossary sits below the flow: link each term the first time the page uses it.
    head, sep, rest = page.partition('<main')
    body, sep2, tail = rest.partition('id="rules"')
    return head + sep + link_terms(body) + sep2 + tail
