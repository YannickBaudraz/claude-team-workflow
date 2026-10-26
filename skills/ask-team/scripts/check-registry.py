#!/usr/bin/env python3
"""Check REGISTRY.md against what is installed and configured.

For every skill row: the skill exists on disk (or is built in), its visibility
matches its frontmatter and ~/.claude/settings.json, every skill it calls can
actually be called, and it says what it does. Every skill SKILL.md names is in
the registry, the step contracts close (check-contracts.py), and the workflow page
can still be built from SKILL.md and the registry. Exit code 1 when anything is wrong.
"""
import glob
import json
import os
import re
import subprocess
import sys

HOME = os.path.expanduser("~")
REGISTRY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "REGISTRY.md")
ROUTER = [os.path.join(os.path.dirname(REGISTRY), name) for name in ("SKILL.md", "ROUTER.md", "FLOW.md")]
# The repo this skill is linked from: <repo>/skills/ask-team/scripts/check-registry.py
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
BUILD_PAGE = os.path.join(REPO, "docs", "build-workflow.py")
CONTRACTS = os.path.join(os.path.dirname(os.path.realpath(__file__)), "check-contracts.py")
SETTINGS = json.load(open(f"{HOME}/.claude/settings.json"))
PLUGINS = json.load(open(f"{HOME}/.claude/plugins/installed_plugins.json"))["plugins"]
OVERRIDES = SETTINGS.get("skillOverrides", {})
DENIED = set(SETTINGS.get("permissions", {}).get("deny", []))
ENABLED = SETTINGS.get("enabledPlugins", {})
MARKETPLACES = json.load(open(f"{HOME}/.claude/plugins/known_marketplaces.json"))
THIS_REPO = "YannickBaudraz/claude-team-workflow"


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


def community_sources():
    """Skill name -> the repo install/community-skills.txt installs it from."""
    sources = {}
    path = os.path.join(REPO, "install", "community-skills.txt")
    for line in open(path) if os.path.exists(path) else []:
        if line.strip() and not line.startswith("#"):
            repo, *skills = line.split()
            sources.update({skill: repo for skill in skills})
    return sources


COMMUNITY = community_sources()


def marketplace_plugin_paths(repo, plugin=None):
    """Install paths of the enabled plugins from the marketplace hosted in `repo`."""
    for market, info in MARKETPLACES.items():
        if info.get("source", {}).get("repo") != repo:
            continue
        for plugin_id, entries in PLUGINS.items():
            name, _, plugin_market = plugin_id.partition("@")
            if plugin_market == market and ENABLED.get(plugin_id) and plugin in (None, name):
                yield entries[0]["installPath"]


def skill_file(row):
    """Where the skill's SKILL.md is installed from its Source, "" when missing, None when built in,
    False when its plugin is disabled.
    Also records a problem when the skill is installed from somewhere other than its Source."""
    command, source = row["command"].lstrip("/"), row["source"].strip("`")
    name, plugin = bare(command), command.split(":")[0] if ":" in command else None
    if source == "Claude Code":
        return None
    if source == "anthropics/knowledge-work-plugins":
        # A synced plugin stays on disk when the user disables it: settings then say false.
        if ENABLED.get(f"{plugin}@synced") is False:
            problems.append(f"{row['command']}: the {plugin} plugin is disabled in settings")
            return False
        candidates = [path for path in glob.glob(f"{HOME}/.claude/plugins/synced/*/{plugin}/skills/{name}/SKILL.md")
                      if any(json.load(open(meta)).get("marketplace_name") == source.split("/")[1]
                             for meta in glob.glob(f"{path.split('/skills/')[0]}*.meta.json"))]
    elif source == "anthropics/skills":
        candidates = glob.glob(f"{HOME}/.claude/skills/synced/*/{name}/SKILL.md")
    else:
        # A plugin from the marketplace in that repo, or else a skill installed in ~/.claude/skills.
        candidates = [path for root in marketplace_plugin_paths(source, plugin)
                      for path in glob.glob(f"{root}/skills/**/{name}/SKILL.md", recursive=True)]
        if plugin or candidates:
            return candidates[0] if candidates else ""
        candidates = [f"{HOME}/.claude/skills/{name}/SKILL.md"]
        link = os.path.realpath(f"{HOME}/.claude/skills/{name}")
        if source == THIS_REPO and not link.startswith(REPO + os.sep):
            problems.append(f"{row['command']}: Source is this repo, but ~/.claude/skills/{name} is not linked to it")
        elif name in COMMUNITY and COMMUNITY[name] != source:
            problems.append(f"{row['command']}: Source says {source}, install/community-skills.txt says {COMMUNITY[name]}")
    found = [c for c in candidates if os.path.exists(c)]
    return found[0] if found else ""


def command_only(path):
    text = open(path).read()
    front = re.match(r"---\n(.*?)\n---", text, re.S)
    return bool(front and re.search(r"^disable-model-invocation:\s*true", front.group(1), re.M))


problems, table = [], {}
for row in rows():
    # Keyed by the full name: engineering:code-review and code-review are different skills.
    table[row["command"].lstrip("/")] = row
for key, row in table.items():
    name = bare(key)
    if row["does"] == "":
        problems.append(f"{row['command']}: no Does line")
    visibility = row["visibility"]
    path = skill_file(row)
    if path == "":
        problems.append(f"{row['command']}: not found for source '{row['source']}'")
        continue
    if path is False:
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
for token in re.findall(r"`([^`]+)`", "\n".join(open(path).read().split("## Maintenance")[0] for path in ROUTER)):
    first = token.split(" ")[0]
    if first.startswith("/") or re.fullmatch(r"[a-z][a-z0-9-]*(:[a-z0-9-]+)?", token):
        named.add(first)
for command in sorted(named):
    if command.lstrip("/") not in table:
        problems.append(f"the router names {command}, which is missing from the registry")

contracts = subprocess.run([sys.executable, CONTRACTS], capture_output=True, text=True)
problems += [line[len("PROBLEM "):] for line in contracts.stdout.splitlines() if line.startswith("PROBLEM ")]
if contracts.returncode and not contracts.stdout.count("PROBLEM "):
    problems.append((contracts.stderr or contracts.stdout).strip())

if os.path.exists(BUILD_PAGE):
    page = subprocess.run([sys.executable, BUILD_PAGE, "--check"], capture_output=True, text=True)
    if page.returncode:
        problems.append((page.stdout or page.stderr).strip())

print(f"{len(table)} skills checked")
for problem in problems:
    print("PROBLEM", problem)
sys.exit(1 if problems else 0)
