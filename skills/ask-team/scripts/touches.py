#!/usr/bin/env python3
"""Count the developer's touches per ticket from Claude Code transcripts, for the
measure docs/measures.md defines. Read-only: it writes nothing.

A touch is one act by the developer on one ticket's work, up to its merge:
- prompt: a prompt or slash command the developer typed in a session, including one
  typed while the agent was working (queued);
- shell: a command the developer ran in shell mode ("!");
- outside: an act on the ticket's PR or tracker item that no session made, such as a
  status changed by hand or a comment typed on the web;
- merge: the merge, exactly one, however it was made. A shell command that merged the PR,
  or the prompt that asked an agent to merge it, is that merge and is not counted again.

Not touches: what an agent runs, even under the developer's login (tool calls, commits,
PR reviews, tracker saves), tool results, skill bodies and other meta entries, command
output, task notifications, interrupt markers, subagent entries, and bots.

An entry belongs to the item its session last named, in a prompt, a shell command or an
agent's command: a ticket's tracker id or PR number, or another item, which leaves the
entry to no ticket. Until its session names an item, an entry belongs to the ticket whose
branch or worktree it ran in, from the branch's first entry; otherwise it counts from the
ticket's claim.

Usage:
  touches.py TICKETS.json TRANSCRIPT_DIR [TRANSCRIPT_DIR...]

TICKETS.json, kept out of the repo because it names real tickets:
  {"tickets": [{"id": "ABC-7", "branch": "abc-7-", "pr": 12,
                "claimed": "2026-01-05T09:00:00Z", "merged": "2026-01-06T18:00:00Z"}],
   "events": [{"ticket": "ABC-7", "kind": "merge", "at": "2026-01-06T18:00:00Z"},
              {"ticket": "ABC-7", "kind": "state", "at": "2026-01-06T17:40:00Z"}]}
"branch" is a regular expression matched against the git branch and the working directory.
"events" are the PR's and the tracker item's own events, read from the code host and the
tracker, without bots; an event within WINDOW seconds of a session's command that changes
the same ticket's PR or tracker item is that command's, not an outside act.

Prints counts only, never text from the transcripts. Reads the entry fields in FIELDS, and
from message content only the text a user entry carries, an agent's Bash commands, tool
names and the item id a tracker tool was given; from a queued prompt, its text and how it
was typed. No usage or cost figure is read.
"""
import datetime
import glob
import json
import os
import re
import sys

FIELDS = ("uuid", "type", "timestamp", "gitBranch", "cwd", "sessionId", "isSidechain", "isMeta", "version")
WINDOW = 120
# Entries the developer did not type: Claude Code writes them into the user's turn.
NOT_TYPED = re.compile(r"\s*(<(bash-stdout|bash-stderr|local-command-[a-z]+|task-notification|system-reminder)\b"
                       r"|\[Request interrupted)")
SHELL = re.compile(r"\s*<bash-input>")
MERGE = re.compile(r"\bgh\s+pr\s+merge\b")
# A command or tool that changes something on the code host or the tracker: an event it caused is
# not an outside act. Reading (gh pr view, list_issues) causes no event.
HOST_COMMAND = re.compile(r"\bgh\s+(pr\s+(create|merge|comment|review|ready|edit|close|reopen)"
                          r"|issue\s+(create|edit|comment|close|reopen)|api\b.*-X\s*(POST|PATCH|PUT|DELETE))\b")
HOST_TOOL = re.compile(r"^mcp__.*(linear|github|jira|atlassian|notion).*__(save|create|update|delete|add|set|transition|edit)",
                       re.I)
PR_REFERENCE = re.compile(r"(?:#|\bPR\s*|/pull/|\bgh\s+pr\s+\w+\s+)(\d+)\b", re.I)


def when(stamp):
    moment = datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    return moment if moment.tzinfo else moment.replace(tzinfo=datetime.timezone.utc)


def entries(directories):
    """Every transcript entry once, by uuid: resumed and forked sessions copy entries."""
    seen = {}
    for directory in directories:
        for path in sorted(glob.glob(os.path.join(directory, "**", "*.jsonl"), recursive=True)):
            for line in open(path, encoding="utf-8"):
                try:
                    raw = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(raw, dict) or not raw.get("uuid") or raw["uuid"] in seen:
                    continue
                try:
                    when(raw.get("timestamp") or "")
                except ValueError:
                    continue
                entry = {key: raw.get(key) for key in FIELDS}
                entry.update(content(raw))
                seen[raw["uuid"]] = entry
    return sorted(seen.values(), key=lambda entry: when(entry["timestamp"]))


def content(raw):
    """What the entry says, read field by field: never the whole message or attachment."""
    found = {"texts": [], "commands": [], "tools": [], "tool_items": [], "shape": "none", "queued": None}
    if raw.get("type") == "attachment":
        attachment = raw.get("attachment") if isinstance(raw.get("attachment"), dict) else {}
        if attachment.get("type") == "queued_command":
            origin = attachment.get("origin") if isinstance(attachment.get("origin"), dict) else {}
            human = attachment.get("humanTurn") is True and origin.get("kind") == "human"
            found["queued"] = attachment.get("commandMode") if human else "not typed"
            prompt = attachment.get("prompt")
            found["texts"] = [prompt] if isinstance(prompt, str) else [
                block.get("text", "") for block in prompt or [] if isinstance(block, dict) and block.get("type") == "text"]
        return found
    message = raw.get("message") if isinstance(raw.get("message"), dict) else {}
    body = message.get("content")
    if isinstance(body, str):
        found.update(texts=[body], shape="text")
    elif isinstance(body, list):
        blocks = [block for block in body if isinstance(block, dict)]
        uses = [block for block in blocks if block.get("type") == "tool_use"]
        inputs = [use.get("input") if isinstance(use.get("input"), dict) else {} for use in uses]
        found.update(
            texts=[block.get("text", "") for block in blocks if block.get("type") == "text"] if raw.get("type") == "user" else [],
            commands=[str(given.get("command", "")) for use, given in zip(uses, inputs) if use.get("name") == "Bash"],
            tools=[str(use.get("name", "")) for use in uses],
            tool_items=[str(given[key]) for given in inputs for key in ("id", "issueId", "identifier") if given.get(key)],
            shape="tool_result" if any(block.get("type") == "tool_result" for block in blocks) else "text")
    return found


def kind(entry):
    """prompt, shell, agent, or the reason the entry is neither the developer's nor an agent's act."""
    if entry["type"] == "attachment" and entry["queued"]:
        if entry["isSidechain"]:
            return "subagent"
        return {"prompt": "prompt", "bash": "shell"}.get(entry["queued"], "not typed")
    if entry["type"] == "assistant":
        return "subagent" if entry["isSidechain"] else "agent"
    if entry["type"] != "user":
        return "other"
    if entry["isSidechain"]:
        return "subagent"
    if entry["isMeta"]:
        return "meta"
    if entry["shape"] == "tool_result":
        return "tool result"
    text = entry["texts"][0] if entry["texts"] else ""
    if not isinstance(text, str) or not text.strip():
        return "unknown shape"
    if SHELL.match(text):
        return "shell"
    if NOT_TYPED.match(text):
        return "not typed"
    return "prompt"


def item_pattern(tickets):
    """Tracker ids with the prefix of the tickets' ids (ABC-7, AB2-7), or None."""
    prefixes = sorted({match.group(1) for match in (re.match(r"(.+-)\d+$", ticket["id"]) for ticket in tickets) if match})
    return re.compile(r"\b(?:" + "|".join(map(re.escape, prefixes)) + r")\d+\b", re.I) if prefixes else None


def last_named(tickets, ids, strings):
    """The ticket the last reference in these strings names, None when it names another item,
    False when there is none. A reference is a PR as #N, PR N, pull/N or gh pr <verb> N, or a
    tracker id with the prefix of the tickets' ids."""
    found = False
    for string in strings:
        references = [(m.start(), "pr", m.group(1)) for m in PR_REFERENCE.finditer(string)]
        references += [(m.start(), "id", m.group(0)) for m in ids.finditer(string)] if ids else []
        if references:
            _, form, value = max(references)
            found = next((t for t in tickets if (form == "pr" and str(t.get("pr")) == value)
                          or (form == "id" and t["id"].lower() == value.lower())), None)
    return found


def count(config, directories):
    tickets = config["tickets"]
    for ticket in tickets:
        ticket["start"], ticket["end"] = when(ticket["claimed"]), when(ticket["merged"])
    by_id = {ticket["id"]: ticket for ticket in tickets}
    ids = item_pattern(tickets)
    merged_at = {ticket["id"]: ticket["end"] for ticket in tickets}
    for event in config.get("events", []):
        if event["kind"] == "merge" and event["ticket"] in by_id:
            merged_at[event["ticket"]] = when(event["at"])

    skipped, unattributed = {}, 0
    session_item, counted, host_acts, agent_merges = {}, [], [], []
    for entry in entries(directories):
        at, what = when(entry["timestamp"]), kind(entry)
        session = entry["sessionId"]
        if what not in ("prompt", "shell", "agent"):
            skipped[what] = skipped.get(what, 0) + 1
            continue
        said = entry["texts"] if what != "agent" else entry["commands"] + entry["tool_items"]
        reference = last_named(tickets, ids, said)
        if reference is not False:
            session_item[session] = reference and reference["id"]
        place = f"{entry['gitBranch'] or ''} {entry['cwd'] or ''}"
        on_branch = next((t for t in tickets if re.search(t["branch"], place)), None)
        if session in session_item:
            owner, how = by_id.get(session_item[session]), "name"
        else:
            owner, how = on_branch, "branch"
        commands = entry["commands"] + (entry["texts"] if what == "shell" else [])
        if any(HOST_COMMAND.search(command) for command in commands) or any(HOST_TOOL.search(tool) for tool in entry["tools"]):
            host_acts.append((at, owner and owner["id"]))
        if what == "agent":
            if owner and any(MERGE.search(command) for command in commands):
                agent_merges.append((at, session, owner["id"]))
            continue
        in_window = owner and at <= owner["end"] and (at >= owner["start"] or owner is on_branch)
        if not in_window:
            unattributed += 1
            continue
        counted.append({"ticket": owner["id"], "kind": what, "at": at, "session": session, "how": how,
                        "version": entry["version"], "merging": any(MERGE.search(command) for command in commands)})

    for ticket in tickets:
        merge = merged_at[ticket["id"]]
        mine = [record for record in counted if record["ticket"] == ticket["id"]]
        shell_merges = [r for r in mine if r["kind"] == "shell" and r["merging"]
                        and abs((r["at"] - merge).total_seconds()) <= WINDOW]
        asked = [m for m in agent_merges if m[2] == ticket["id"] and abs((m[0] - merge).total_seconds()) <= WINDOW]
        if shell_merges:
            min(shell_merges, key=lambda r: abs((r["at"] - merge).total_seconds()))["kind"] = "merge"
        elif asked:
            at, session, _ = asked[-1]
            before = [r for r in mine if r["session"] == session and r["kind"] == "prompt" and r["at"] <= at]
            if before:
                before[-1]["kind"] = "merge"

    report = {ticket["id"]: {"prompt": 0, "shell": 0, "outside": 0, "merge": 1} for ticket in tickets}
    ways = {ticket["id"]: {"branch": 0, "name": 0} for ticket in tickets}
    for record in counted:
        if record["kind"] != "merge":
            report[record["ticket"]][record["kind"]] += 1
            ways[record["ticket"]][record["how"]] += 1
    for event in config.get("events", []):
        if event["kind"] == "merge" or event["ticket"] not in by_id:
            continue
        at, ticket = when(event["at"]), by_id[event["ticket"]]
        if not ticket["start"] <= at <= ticket["end"]:
            continue
        if not any(abs((at - other).total_seconds()) <= WINDOW and owner in (ticket["id"], None)
                   for other, owner in host_acts):
            report[ticket["id"]]["outside"] += 1
    versions = sorted({record["version"] for record in counted if record["version"]})
    return report, skipped, unattributed, versions, ways


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__.split("Usage:")[1].split("TICKETS.json,")[0].strip())
    config = json.load(open(sys.argv[1], encoding="utf-8"))
    report, skipped, unattributed, versions, ways = count(config, sys.argv[2:])
    print("| Ticket | Prompts | Shell | Outside | Merge | Touches |")
    print("|---|---|---|---|---|---|")
    for ticket, counts in report.items():
        print(f"| {ticket} | {counts['prompt']} | {counts['shell']} | {counts['outside']} | {counts['merge']} "
              f"| {sum(counts.values())} |")
    print()
    for ticket, way in ways.items():
        print(f"{ticket}: {way['branch']} prompts and shell commands by branch or worktree, {way['name']} by a named item")
    print(f"Unattributed typed entries: {unattributed}")
    print("Not counted: " + ", ".join(f"{reason} {number}" for reason, number in sorted(skipped.items())))
    print(f"Claude Code versions in the counted sessions: {', '.join(versions) or 'none'}")


if __name__ == "__main__":
    main()
