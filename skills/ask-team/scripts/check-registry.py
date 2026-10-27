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
def plugin_file(name, default):
    """A file in ~/.claude/plugins, or `default` before Claude Code has written it (a fresh machine)."""
    path = f"{HOME}/.claude/plugins/{name}"
    return json.load(open(path)) if os.path.exists(path) else default


PLUGINS = plugin_file("installed_plugins.json", {"plugins": {}})["plugins"]
OVERRIDES = SETTINGS.get("skillOverrides", {})
DENIED = set(SETTINGS.get("permissions", {}).get("deny", []))
ENABLED = SETTINGS.get("enabledPlugins", {})
MARKETPLACES = plugin_file("known_marketplaces.json", {})
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
    """Skill name -> the repo install/community-skills.txt installs it from.
    Also records a problem for a source not pinned to a full commit (D71)."""
    sources = {}
    path = os.path.join(REPO, "install", "community-skills.txt")
    for line in open(path) if os.path.exists(path) else []:
        if line.strip() and not line.startswith("#"):
            source, *skills = line.split()
            repo, _, commit = source.partition("#")
            if not re.fullmatch(r"[0-9a-f]{40}", commit):
                problems.append(f"install/community-skills.txt: {repo} is not pinned to a full commit")
            sources.update({skill: repo for skill in skills})
    return sources


def marketplace_plugin_paths(repo, plugin=None):
    """Install paths of the enabled plugins from the marketplace hosted in `repo`, or declared in
    settings with plugin entries that point at `repo` (a marketplace pinned to a commit)."""
    for market, info in MARKETPLACES.items():
        source = info.get("source", {})
        repos = {source.get("repo")} | {entry["source"].get("repo") for entry in source.get("plugins", [])
                                        if isinstance(entry.get("source"), dict)}
        if repo not in repos:
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
        # A denied duplicate is meant never to fire, so a disabled plugin suits it.
        if ENABLED.get(f"{plugin}@synced") is False:
            if row["visibility"] != "denied":
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
COMMUNITY = community_sources()
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

# Plugins the settings fragment pins to a commit must be installed at that commit (D71).
fragment = os.path.join(REPO, "install", "settings-fragment.json")
for market, info in (json.load(open(fragment)).get("extraKnownMarketplaces", {}) if os.path.exists(fragment) else {}).items():
    for plugin in info["source"].get("plugins", []):
        sha, plugin_id = plugin["source"].get("sha"), f"{plugin['name']}@{market}"
        installed = PLUGINS.get(plugin_id, [{}])[0].get("gitCommitSha")
        if sha and installed != sha:
            problems.append(f"{plugin_id}: installed at {(installed or 'nothing')[:7]}, "
                            f"install/settings-fragment.json pins {sha[:7]}; run install.sh")

# The merge guard (D8): its hook is in the user settings for Bash, Monitor and MCP tools, refuses
# when it fails, and runs the copy install.sh made of this repo's version.
GUARD = os.path.join(REPO, "skills", "ask-team", "hooks", "merge-guard.py")
INSTALLED_GUARD = f"{HOME}/.claude/hooks/merge-guard.py"
guard_entries = [(entry.get("matcher") or "", hook) for entry in SETTINGS.get("hooks", {}).get("PreToolUse", [])
                 for hook in entry.get("hooks", []) if "merge-guard.py" in hook.get("command", "")]
if not guard_entries:
    problems.append("the merge guard's PreToolUse hook is missing from ~/.claude/settings.json; run install.sh")
def matches(matcher, tool):
    """Whether a hook matcher covers the tool, as Claude Code reads it: empty or * is every tool,
    a plain list is exact names, anything else an unanchored regular expression."""
    if matcher in ("", "*"):
        return True
    if not re.search(r"[^A-Za-z0-9_|, -]", matcher):
        return tool in {name.strip() for name in re.split(r"[|,]", matcher)}
    try:
        return bool(re.search(matcher, tool))
    except re.error:
        return False


for matcher, hook in guard_entries:
    missed = [tool for tool in ("Bash", "Monitor", "mcp__github__merge_pull_request") if not matches(matcher, tool)]
    if missed:
        problems.append(f"the merge guard's hook matcher {matcher!r} misses {', '.join(missed)}")
    if hook.get("onFailure") != "block":
        problems.append("the merge guard's hook lets a call through when it fails: set \"onFailure\": \"block\"")
if os.path.exists(GUARD) and (not os.path.exists(INSTALLED_GUARD)
                              or open(GUARD, "rb").read() != open(INSTALLED_GUARD, "rb").read()):
    problems.append("~/.claude/hooks/merge-guard.py is missing or differs from this repo's; run install.sh")

# The Claude Code version the workflow was last checked on. A difference is a note, not a problem:
# Claude Code still updates itself.
notes = []
checked_version = os.path.join(REPO, "install", "claude-code-version.txt")
if os.path.exists(checked_version):
    wanted = open(checked_version).read().strip()
    try:
        running = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.split(" ")[0].strip()
    except OSError:
        running = ""
    if running != wanted:
        notes.append(f"Claude Code is {running or 'not found'}, the workflow was last checked on {wanted} "
                     "(install/claude-code-version.txt)")

print(f"{len(table)} skills checked")
for note in notes:
    print("NOTE", note)
for problem in problems:
    print("PROBLEM", problem)
sys.exit(1 if problems else 0)
