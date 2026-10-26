"""Reading the sources: the router (SKILL.md), the registry and the README's Install section."""
import re

from .config import ROLE_WORDS


class SourceError(Exception):
    pass


def need(ok, message):
    if not ok:
        raise SourceError(message)


def section(text, title):
    match = re.search(rf'^## {re.escape(title)}\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    need(match, f'SKILL.md has no "## {title}" section')
    return match.group(1).strip()


def sentences(text):
    text = ' '.join(text.split())
    return [sentence for sentence in re.split(r'(?<=[.!?])\s+(?=[A-Z`*])', text) if sentence]


def read_router(paths):
    """The router's files, SKILL.md first, as one text without their frontmatter."""
    text = '\n'.join(re.sub(r'\A---\n.*?\n---\n', '', open(path, encoding='utf-8').read(), flags=re.S)
                     for path in paths)
    intro = text.split('## How to route')[0]
    never = [sentence for sentence in sentences(intro) if 'never runs' in sentence]
    need(never, 'SKILL.md no longer says the router never runs the step')

    items = re.findall(r'^\d+\. \*\*(.+?)\*\*\s*(.*)$', section(text, 'How to route'), re.M)
    need(len(items) >= 2, 'How to route should be a numbered list with bold lead-ins')
    answer = [rest for lead, rest in items if lead.lower().startswith('answer')]
    answer_with = re.match(r'with:\s*(.+?)\.(?:\s|$)', answer[0]) if answer else None
    need(answer_with, 'How to route has no "Answer with: ..." item')
    # "the step and why it is next, the exact command ..., and what ..." -> its parts.
    answer = [re.sub(r'\s*\([^)]*\)', '', part).strip()
              for part in re.split(r',\s*(?:and\s+)?', answer_with.group(1))]
    sizing = [rest for lead, rest in items if lead.lower().startswith('size')]
    need(sizing, 'How to route has no "Size the request" item')
    fork, fork_notes = [], []
    for sentence in sentences(sizing[0]):
        size = re.search(r'\*(\w+)\*', sentence)
        if size:
            fork.append((size.group(1).capitalize(), sentence))
        else:
            fork_notes.append(sentence)
    need(fork, 'Size the request names no sizes in *italics*')

    flow = section(text, 'Main flow')
    steps = {}
    for line in flow.splitlines():
        row = re.match(r'\|\s*(\d+)\s*\|(.*)\|\s*$', line)
        if not row:
            continue
        number = int(row.group(1))
        cells = [cell.strip() for cell in row.group(2).split('|')]
        need(len(cells) == 3, f'Main flow row {number} should have four columns')
        step, command, output = cells
        note = ''
        if '(' in step:
            step, note = step.split('(', 1)
            note = note.rstrip(')').strip()
        name, _, qual = (part.strip() for part in step.partition(','))
        steps[number] = dict(
            number=number, name=name, qual=qual, note=note,
            optional=note.lower().startswith('only'), command=command, output=output,
            # A gate is a step whose output has to be approved, or that you merge.
            gate=bool(re.search(r'\bapproved\b|\bmerges\b', output, re.I)))
    need(list(steps) == list(range(1, len(steps) + 1)), 'Main flow steps should be numbered 1, 2, 3...')

    rules_text = '\n'.join(line for line in flow.splitlines() if not line.startswith('|'))
    epics = re.search(r'about (\d+) epics per roadmap', rules_text)
    most = re.search(r'never more than (\d+)', rules_text)
    need(epics and most, 'Main flow no longer states the epics-per-roadmap preference')

    sessions = section(text, 'Sessions')
    roles = {}
    found = re.findall(r'\b(product|tech lead|developer|reviewer)\b[^()]*\((?:steps )?(\d+)(?: to (\d+))?',
                       ' '.join(sessions.split()))
    for word, lo, hi in found:
        for number in range(int(lo), int(hi or lo) + 1):
            roles[number] = ROLE_WORDS[word]
    need(set(roles.values()) == set(ROLE_WORDS.values()),
         'Sessions no longer names the product, tech lead, developer and reviewer steps')
    for number in steps:
        steps[number]['role'] = roles.get(number, 'you')

    per_epic = [number for number, step in steps.items() if step['qual'] == 'per epic']
    per_ticket = [number for number, step in steps.items() if step['qual'] == 'per ticket']
    need(per_epic and len(per_ticket) == 1,
         'Main flow should mark the epic steps "per epic" and the first ticket step "per ticket"')
    first, last, tick = min(per_epic), max(per_epic), per_ticket[0]
    need(last == max(steps) and first < tick < last,
         'The per-epic steps should close the flow and contain the per-ticket step')
    review = [number for number in range(tick, last) if steps[number]['role'] == 'review']
    need(review, 'No reviewer step inside the ticket loop')

    return dict(
        never=never[0], answer=answer, beats=[lead.rstrip('.') for lead, _ in items], fork=fork,
        fork_notes=fork_notes, steps=steps, epics=epics.group(1), most=most.group(1),
        project=[number for number in steps if number < first], lead=list(range(first, tick)),
        ticket=list(range(tick, last)), close=last, review=review[0],
        ways=[line[2:].strip() for line in section(text, 'Ways in').splitlines() if line.startswith('- ')],
        any_time=re.findall(r'`([^`]+)`(?: \(([^)]*)\))?', section(text, 'Any time')),
        gate_rules=sentences(rules_text), session_rules=sentences(sessions))


def read_registry(path, steps):
    tables, header = [], None
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if not line.startswith('|'):
            header = None
            continue
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        if header is None:
            header = [cell.lower() for cell in cells]
            tables.append([])
        elif not all(set(cell) <= set('-: ') for cell in cells):
            tables[-1].append(dict(zip(header, cells)))
    workflow = [table for table in tables if table and 'does' in table[0]]
    need(len(workflow) == 1, 'REGISTRY.md should have one table with a Does column')

    groups, kinds, sources = {}, {}, {}
    for row in workflow[0]:
        name, used, does = row['command'].strip('`'), row.get('used at', ''), row.get('does', '')
        need(does, f'REGISTRY.md: {name} has no Does')
        at_step = re.match(r'(\d+)\b[^,]*(?:,\s*(.*))?$', used)
        if at_step:
            key, tag = int(at_step.group(1)), at_step.group(2) or ''
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
    install = re.search(r'^## Install\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    code = install and re.search(r'```\w*\n(.*?)```', install.group(1), re.S)
    if not code:
        return None
    prose = [' '.join(paragraph.split())
             for paragraph in re.sub(r'```.*?```', '', install.group(1), flags=re.S).split('\n\n')
             if paragraph.strip()]
    return dict(needs=prose[0] if prose else '', commands=code.group(1).strip().splitlines(),
                after=prose[1] if len(prose) > 1 else '')
