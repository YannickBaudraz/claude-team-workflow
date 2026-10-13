#!/usr/bin/env python3
"""List the session names of one project, newest first, the way /resume shows them.

    python3 session_titles.py            # the project of the current directory
    python3 session_titles.py <dir>      # another project directory

Each line: last activity, the name (yours from /rename or --name, else the generated
one, else the first prompt), and flags: "this session", "duplicate".

Claude Code keeps each session as ~/.claude/projects/<dir with every non-alphanumeric
character turned into "-">/<session id>.jsonl, with "custom-title" and "ai-title" lines.
That layout is not documented: when it changes, this prints nothing and exits 0, and
the skill names the session without comparing.
"""
import collections
import datetime
import json
import os
import re
import sys

cwd = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
folder = os.path.join(os.path.expanduser('~/.claude/projects'), re.sub(r'[^A-Za-z0-9]', '-', cwd))
current = os.environ.get('CLAUDE_CODE_SESSION_ID', '')


def first_prompt(line):
    """A prompt you typed, not a command wrapper or a tool result."""
    try:
        entry = json.loads(line)
    except ValueError:
        return ''
    content = entry.get('message', {}).get('content')
    if isinstance(content, list):
        content = ' '.join(c.get('text', '') for c in content if isinstance(c, dict) and c.get('type') == 'text')
    if not isinstance(content, str) or content.lstrip().startswith('<'):
        return ''
    return ' '.join(content.split())[:70]


sessions = []
try:
    files = [f for f in os.listdir(folder) if f.endswith('.jsonl')]
except OSError:
    files = []
for name in files:
    path = os.path.join(folder, name)
    custom = generated = prompt = ''
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if '"custom-title"' in line:
                custom = re.search(r'"customTitle":"((?:[^"\\]|\\.)*)"', line)
                custom = json.loads(f'"{custom.group(1)}"') if custom else ''
            elif '"ai-title"' in line:
                found = re.search(r'"aiTitle":"((?:[^"\\]|\\.)*)"', line)
                generated = json.loads(f'"{found.group(1)}"') if found else generated
            elif not prompt and '"type":"user"' in line:
                prompt = first_prompt(line)
    title = custom or generated or (f'"{prompt}"' if prompt else '')
    if not title:
        continue
    when = datetime.datetime.fromtimestamp(os.path.getmtime(path))
    sessions.append((when, title, name[:-6] == current, bool(custom)))

sessions.sort(reverse=True)
count = collections.Counter(t.lower() for _, t, _, _ in sessions)
for when, title, here, named in sessions:
    flags = [f for f, on in (('this session', here), ('duplicate', count[title.lower()] > 1),
                             ('generated', not named and not title.startswith('"'))) if on]
    print(f'{when:%Y-%m-%d %H:%M}  {title}' + (f'  ({", ".join(flags)})' if flags else ''))
