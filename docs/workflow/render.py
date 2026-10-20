"""Drawing helpers: the page's voice, inline markdown, cards, arrows, and step and term links."""
import html
import re

from .config import ROLE_NAMES, STEP_SUMMARIES, TERMS
from .sources import sentences

esc = html.escape


def you(article):
    """"The" or "the" turned into "You" or "you", keeping the capital."""
    return article.replace('t', 'y').replace('T', 'Y')


# SKILL.md speaks to Claude about "the user"; the page speaks to that user.
VOICE = [
    (r'never treat a step as approved because its output exists',
     lambda match: 'a step is approved when you approve it, not when its output exists'),
    (r'\bPast that, propose a split', lambda match: 'Past that, Claude proposes a split'),
    (r"\b([Tt])he user's(?=[:.,;)]|$)", lambda match: you(match.group(1)) + 'ours'),
    (r"\b([Tt])he user's\b", lambda match: you(match.group(1)) + 'our'),
    (r'\b([Tt])he user (is|has|does)\b',
     lambda match: you(match.group(1)) + 'ou ' + {'is': 'are', 'has': 'have', 'does': 'do'}[match.group(2)]),
    (r'\b([Tt])he user (\w+?)s\b', lambda match: you(match.group(1)) + 'ou ' + match.group(2)),
    (r'\b([Tt])he user\b', lambda match: you(match.group(1)) + 'ou'),
]


def voice(text):
    for pattern, replacement in VOICE:
        text = re.sub(pattern, replacement, text)
    return text


def md(text):
    """Inline markdown to HTML: `code` (a command's arguments muted), **bold**, *italics*."""
    out = []
    for segment in re.split(r'(`[^`]*`)', text):
        if len(segment) > 1 and segment[0] == segment[-1] == '`':
            code = segment[1:-1]
            name, _, args = code.partition(' <') if code.startswith('/') else (code, '', '')
            # The space sits inside the span, so a long command breaks before its arguments.
            args = f'<span class="arg"> &lt;{esc(args)}</span>' if args else ''
            out.append(f'<code>{esc(name)}{args}</code>')
        else:
            prose = esc(voice(segment))
            prose = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', prose)
            prose = re.sub(r'\*(.+?)\*', r'<em>\1</em>', prose)
            out.append(prose)
    return ''.join(out)


def cap(text):
    return text[:1].upper() + text[1:]


def shown_output(output):
    """The output without what the gate mark says, and the gate mark's words.

    "Approved.", "reviewed and approved" and "The user merges." move to the mark, which
    reads "You approve", "You approve before publishing" or "You approve, then merge"."""
    keep, when, merge = [], '', False
    for sentence in sentences(output):
        if re.fullmatch(r'(both )?approved( by the user)?\.?', sentence, re.I):
            continue
        if re.fullmatch(r'the user merges\.?', sentence, re.I):
            merge = True
            continue
        approved = re.search(r',?\s*(?:reviewed and )?approved(?: (before \w+))?(?=\.?$)', sentence, re.I)
        if approved:
            when = approved.group(1) or ''
            sentence = sentence[:approved.start()] + sentence[approved.end():]
        keep.append(sentence)
    mark = 'You approve, then merge' if merge else 'You approve' + (f' {when}' if when else '')
    return ' '.join(keep), mark


AI = '<i class="ai"></i>'


def link():
    """A connector between steps. A gate shows on the card before it, not on the arrow."""
    return f'<span class="link">{AI}</span>'


def arr():
    return f'<span class="arr" aria-hidden="true">{link()}</span>'


def card_html(step, level=3):
    number = step['number']
    label = ROLE_NAMES[step['role']] + (f' · {step["qual"]}' if step['qual'] else '')
    note = f'<p class="note">{md(cap(step["note"]))}</p>' if step['note'] else ''
    out, mark = shown_output(step['output'])
    result = (f'<p class="out">{link_steps(md(out))}</p>' if out else '') + (
        f'<p class="gate-mark"><span class="dia"></span>{esc(mark)}</p>' if step['gate'] else '')
    return (f'<article class="card{" optional" if step["optional"] else ""} p-{step["role"]}" id="step-{number}">'
            f'<div class="card-head"><span class="num">{number}</span>'
            f'<span class="role">{esc(label)}</span></div>'
            f'<h{level} class="title"><span class="vh">Step {number}, {esc(label)}: </span>'
            f'<a href="#skills-{number}">{esc(step["name"])}'
            f'<span class="vh">, its skills</span><i class="to-skills"></i></a></h{level}>{note}'
            f'<p class="summary">{link_steps(md(STEP_SUMMARIES[number]))}</p>'
            + (f'<p class="repeat"><i class="loop"></i>Repeats for each {esc(step["qual"][4:])}</p>'
               if step['qual'].startswith('per ') and step['qual'] not in ('per epic', 'per ticket') else '')
            + (f'<div class="result">{result}</div>' if result else '') + '</article>')


def flow_html(router, numbers, cls='flow', level=3):
    cards = [card_html(router['steps'][number], level) for number in numbers]
    joins = [arr() for _ in numbers[:-1]]
    return f'<div class="{cls}">' + ''.join(card + join for card, join in zip(cards, joins + [''])) + '</div>'


def link_steps(markup):
    """Link "step 9", "steps 6 to 9" and "(10" in running text to the step's card."""
    def one(reference):
        lead, number = reference.group(1), int(reference.group(2))
        if not 1 <= number <= STEP_COUNT:
            return reference.group(0)
        if lead == '(':
            return f'(<a class="step-ref" href="#step-{number}">{reference.group(0)[1:]}</a>'
        return f'<a class="step-ref" href="#step-{number}">{reference.group(0)}</a>'
    parts = re.split(r'(<[^>]+>)', markup)
    depth = 0
    for index, part in enumerate(parts):
        if part.startswith('<'):
            depth += 1 if re.match(r'<(a|code)\b', part) else -1 if re.match(r'</(a|code)>', part) else 0
        elif depth == 0:
            parts[index] = re.sub(r'(\b[Ss]teps? |\()(\d{1,2})(?: to \d{1,2})?(?=[\s),.;:])', one, part)
    return ''.join(parts)


STEP_COUNT = 0
TERM_SKIP = re.compile(r'<(a|code|h[1-4]|title|script|style|summary)\b|class="[^"]*\b(role|num|tag|beats|cmd)\b')


def link_terms(markup):
    """Link the first use of each glossary term, outside headings, links and code."""
    todo = [(term, re.compile(rf'(?i){pattern}')) for term, pattern, _ in TERMS]
    parts = re.split(r'(<[^>]+>)', markup)
    stack = []
    for index, part in enumerate(parts):
        if part.startswith('</'):
            if stack:
                stack.pop()
        elif part.startswith('<'):
            if not re.match(r'<(input|br|img|meta|link|!)', part, re.I) and not part.endswith('/>'):
                stack.append(bool(TERM_SKIP.match(part) or TERM_SKIP.search(part)))
        elif part.strip() and not any(stack):
            # Find every term in the original text first, so no link lands inside another.
            hits = sorted((found.start(), found.end(), term, pattern)
                          for term, pattern in todo for found in [pattern.search(part)] if found)
            out, at = [], 0
            for start, end, term, pattern in hits:
                if start < at:
                    continue
                out += [part[at:start], f'<a class="term" href="#term-{slug(term)}">{part[start:end]}</a>']
                at = end
                todo.remove((term, pattern))
            parts[index] = ''.join(out) + part[at:]
    return ''.join(parts)


def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def answer_html(router):
    """What the router's answer holds, as SKILL.md lists it."""
    items = ''.join(f'<li>{md(cap(part))}</li>' for part in router['answer'])
    return f'<div class="answer"><p class="answer-title">Its answer gives you</p><ol>{items}</ol></div>'
