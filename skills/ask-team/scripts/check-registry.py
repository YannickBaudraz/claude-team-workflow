#!/usr/bin/env python3
"""Check REGISTRY.md against what is installed and configured.

For every skill row: the skill exists on disk (or is built in), its visibility
matches its frontmatter and ~/.claude/settings.json, and every skill it calls
can actually be called. Exit code 1 when anything is wrong.
"""
import glob
import json
import os
import re
import sys

HOME = os.path.expanduser("~")
REGISTRY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "REGISTRY.md")
SETTINGS = json.load(open(f"{HOME}/.claude/settings.json"))
PLUGINS = json.load(open(f"{HOME}/.claude/plugins/installed_plugins.json"))["plugins"]
OVERRIDES = SETTINGS.get("skillOverrides", {})
DENIED = set(SETTINGS.get("permissions", {}).get("deny", []))
ENABLED = SETTINGS.get("enabledPlugins", {})


def rows():
    for line in open(REGISTRY):
        if line.startswith("| `"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            yield {"command": cells[0].strip("`"), "source": cells[1],
                   "visibility": cells[2], "calls": cells[4] if len(cells) > 5 else ""}


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

print(f"{len(table)} skills checked")
for problem in problems:
    print("PROBLEM", problem)
sys.exit(1 if problems else 0)
