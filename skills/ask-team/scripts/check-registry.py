#!/usr/bin/env python3
"""Check REGISTRY.md against what is installed and configured.

For every skill row: the skill exists on disk (or is built in), its visibility
matches its frontmatter and ~/.claude/settings.json, every skill it calls can
actually be called, and it says what it does. Every skill SKILL.md names is in
the registry, and the workflow page can still be built from SKILL.md and the
registry. Exit code 1 when anything is wrong.
"""
import glob
import json
import os
import re
import subprocess
import sys

HOME = os.path.expanduser("~")
REGISTRY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "REGISTRY.md")
SKILL = os.path.join(os.path.dirname(REGISTRY), "SKILL.md")
# The repo this skill is linked from: <repo>/skills/ask-team/scripts/check-registry.py
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
BUILD_PAGE = os.path.join(REPO, "docs", "build-workflow.py")
SETTINGS = json.load(open(f"{HOME}/.claude/settings.json"))
PLUGINS = json.load(open(f"{HOME}/.claude/plugins/installed_plugins.json"))["plugins"]
OVERRIDES = SETTINGS.get("skillOverrides", {})
DENIED = set(SETTINGS.get("permissions", {}).get("deny", []))
ENABLED = SETTINGS.get("enabledPlugins", {})


def rows():
    """The skill rows of every table, keyed by the table's column headers."""
    header = None
    for line in open(REGISTRY):
        line = line.strip()
        if not line.startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
        elif cells[0].startswith("`"):
            row = dict(zip(header, cells))
            yield {"command": cells[0].strip("`"), "source": row["source"],
                   "visibility": row["visibility"], "calls": row.get("calls", ""),
                   "does": row.get("does")}


def bare(command):
    return command.lstrip("/").split(":")[-1]


def enabled_plugin_path(plugin):
    for plugin_id, entries in PLUGINS.items():
        if plugin_id.split("@")[0] == plugin and ENABLED.get(plugin_id):
            return entries[0]["installPath"]
    return None


def skill_file(row):
    name, source = bare(row["command"]), row["source"]
    if source in ("ours", "personal"):
        candidates = [f"{HOME}/.claude/skills/{name}/SKILL.md"]
    elif source == "matt" or source.startswith("plugin:"):
        root = enabled_plugin_path("mattpocock-skills" if source == "matt" else source.split(":")[1])
        candidates = glob.glob(f"{root}/skills/**/{name}/SKILL.md", recursive=True) if root else []
    elif source == "synced:anthropic-skills":
        candidates = glob.glob(f"{HOME}/.claude/skills/synced/*/{name}/SKILL.md")
    elif source.startswith("synced:"):
        candidates = glob.glob(f"{HOME}/.claude/plugins/synced/*/{source.split(':')[1]}/skills/{name}/SKILL.md")
    else:
        return None
    found = [c for c in candidates if os.path.exists(c)]
    return found[0] if found else ""


def command_only(path):
    text = open(path).read()
    front = re.match(r"---\n(.*?)\n---", text, re.S)
    return bool(front and re.search(r"^disable-model-invocation:\s*true", front.group(1), re.M))


problems, table = [], {}
for row in rows():
    table[bare(row["command"])] = row
for name, row in table.items():
    if row["does"] == "":
        problems.append(f"{row['command']}: no Does line")
    visibility = row["visibility"]
    path = skill_file(row)
    if path == "":
        problems.append(f"{row['command']}: not found for source '{row['source']}'")
        continue
    if visibility == "built-in":
        continue
    overridden = OVERRIDES.get(name, "on") != "on"
    denied = f"Skill({row['command'].lstrip('/')})" in DENIED
    actual = ("denied" if denied else "hidden" if OVERRIDES.get(name) == "user-invocable-only"
              else "typed" if command_only(path) else "auto")
    if actual != visibility or (visibility == "auto" and overridden):
        problems.append(f"{row['command']}: registry says {visibility}, settings and frontmatter say {actual}")
    for callee in filter(None, (c.strip() for c in row["calls"].split(","))):
        if callee.startswith("file:"):
            target = callee[5:]
            if not os.path.exists(f"{HOME}/.claude/skills/{target}/SKILL.md"):
                problems.append(f"{row['command']}: reads {target} from disk, but it is not installed")
        elif callee not in table:
            problems.append(f"{row['command']}: calls {callee}, which is missing from the registry")
        elif table[callee]["visibility"] not in ("auto", "built-in"):
            problems.append(f"{row['command']}: calls {callee}, which is {table[callee]['visibility']} and cannot be called")

# Every command, and every bare skill name, that the router names (Maintenance is about this repo).
named = set()
for token in re.findall(r"`([^`]+)`", open(SKILL).read().split("## Maintenance")[0]):
    first = token.split(" ")[0]
    if first.startswith("/") or re.fullmatch(r"[a-z][a-z0-9-]*(:[a-z0-9-]+)?", token):
        named.add(first)
for command in sorted(named):
    if bare(command) not in table:
        problems.append(f"SKILL.md names {command}, which is missing from the registry")

if os.path.exists(BUILD_PAGE):
    page = subprocess.run([sys.executable, BUILD_PAGE, "--check"], capture_output=True, text=True)
    if page.returncode:
        problems.append((page.stdout or page.stderr).strip())

print(f"{len(table)} skills checked")
for problem in problems:
    print("PROBLEM", problem)
sys.exit(1 if problems else 0)
