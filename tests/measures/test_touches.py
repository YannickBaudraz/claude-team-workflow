"""Unit tests for skills/ask-team/scripts/touches.py, on invented transcripts only.

Run: python3 -m unittest discover tests/measures
"""
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "..", "skills", "ask-team", "scripts", "touches.py")
spec = importlib.util.spec_from_file_location("touches", SCRIPT)
touches = importlib.util.module_from_spec(spec)
spec.loader.exec_module(touches)

TICKET = {"id": "ABC-7", "branch": "abc-7-", "pr": 12,
          "claimed": "2026-01-05T09:00:00Z", "merged": "2026-01-06T18:00:00Z"}
SECRET = "a private sentence that must never be printed"


def user(uuid, at, text, branch="abc-7-add-a-thing", session="s1", **extra):
    return {"uuid": uuid, "type": "user", "timestamp": at, "gitBranch": branch, "cwd": "/repo",
            "sessionId": session, "isSidechain": False, "version": "9.9.9",
            "message": {"role": "user", "content": text}, **extra}


def agent(uuid, at, command=None, tool="Bash", branch="abc-7-add-a-thing", session="s1"):
    block = {"type": "tool_use", "name": tool, "input": {"command": command} if command else {}}
    return {"uuid": uuid, "type": "assistant", "timestamp": at, "gitBranch": branch, "cwd": "/repo",
            "sessionId": session, "isSidechain": False, "version": "9.9.9",
            "message": {"role": "assistant", "content": [block]}}


class Touches(unittest.TestCase):
    def run_on(self, files, events=(), tickets=(TICKET,)):
        directory = tempfile.mkdtemp()
        for name, lines in files.items():
            with open(os.path.join(directory, name), "w", encoding="utf-8") as out:
                out.write("\n".join(json.dumps(line) for line in lines) + "\n")
        config = {"tickets": [dict(ticket) for ticket in tickets], "events": list(events)}
        return touches.count(config, [directory])

    def test_counts_typed_prompts_and_slash_commands(self):
        report, _, _, _, _ = self.run_on({"a.jsonl": [
            user("u1", "2026-01-05T10:00:00Z", "build it"),
            user("u2", "2026-01-05T10:05:00Z", "<command-message>build-ticket</command-message>"),
        ]})
        self.assertEqual(report["ABC-7"]["prompt"], 2)

    def test_skips_what_the_developer_did_not_type(self):
        report, skipped, _, _, _ = self.run_on({"a.jsonl": [
            user("u1", "2026-01-05T10:00:00Z", [{"type": "tool_result", "content": "ok"}]),
            user("u2", "2026-01-05T10:01:00Z", "skill body", isMeta=True),
            user("u3", "2026-01-05T10:02:00Z", "<bash-stdout>done</bash-stdout>"),
            user("u4", "2026-01-05T10:03:00Z", "<task-notification>finished</task-notification>"),
            user("u5", "2026-01-05T10:04:00Z", [{"type": "text", "text": "[Request interrupted by user]"}]),
            user("u6", "2026-01-05T10:05:00Z", "subagent prompt", isSidechain=True),
            user("u7", "2026-01-05T10:06:00Z", "<local-command-stdout>set</local-command-stdout>"),
        ]})
        self.assertEqual(report["ABC-7"]["prompt"], 0)
        self.assertEqual(skipped, {"tool result": 1, "meta": 1, "not typed": 4, "subagent": 1})

    def test_resumed_sessions_count_once(self):
        line = user("u1", "2026-01-05T10:00:00Z", "build it")
        report, _, _, _, _ = self.run_on({"a.jsonl": [line], "b.jsonl": [line]})
        self.assertEqual(report["ABC-7"]["prompt"], 1)

    def test_shell_counts_and_a_shell_merge_is_the_one_merge(self):
        report, _, _, _, _ = self.run_on({"a.jsonl": [
            user("u1", "2026-01-05T10:00:00Z", "<bash-input>npm test</bash-input>"),
            user("u2", "2026-01-06T17:59:00Z", "<bash-input>gh pr merge 12 --merge</bash-input>"),
        ]}, events=[{"ticket": "ABC-7", "kind": "merge", "at": "2026-01-06T17:59:30Z"}])
        self.assertEqual(report["ABC-7"], {"prompt": 0, "shell": 1, "outside": 0, "merge": 1})

    def test_a_merge_on_the_web_is_still_one_merge_and_not_outside(self):
        report, _, _, _, _ = self.run_on({"a.jsonl": [user("u1", "2026-01-05T10:00:00Z", "build it")]},
                                      events=[{"ticket": "ABC-7", "kind": "merge", "at": "2026-01-06T18:00:00Z"}])
        self.assertEqual(report["ABC-7"]["merge"], 1)
        self.assertEqual(report["ABC-7"]["outside"], 0)

    def test_attribution_by_worktree(self):
        report, _, unattributed, _, _ = self.run_on({"a.jsonl": [
            user("u1", "2026-01-05T10:00:00Z", "go", branch="HEAD", cwd="/repo/.claude/worktrees/abc-7-add"),
        ]})
        self.assertEqual((report["ABC-7"]["prompt"], unattributed), (1, 0))

    def test_a_review_on_another_branch_belongs_to_the_ticket_it_names(self):
        report, _, unattributed, _, _ = self.run_on({"r.jsonl": [
            user("u1", "2026-01-06T09:00:00Z", "something before any ticket is named", branch="HEAD", session="r"),
            agent("a1", "2026-01-06T09:01:00Z", "gh pr checkout 12 --detach", branch="HEAD", session="r"),
            user("u2", "2026-01-06T09:05:00Z", "looks right", branch="HEAD", session="r"),
            user("u3", "2026-01-06T09:06:00Z", "now review PR 13", branch="HEAD", session="r"),
            user("u4", "2026-01-06T09:07:00Z", "and this", branch="HEAD", session="r"),
        ]})
        self.assertEqual(report["ABC-7"]["prompt"], 1)
        self.assertEqual(unattributed, 3)

    def test_entries_after_the_merge_or_before_the_claim_elsewhere_are_not_the_tickets(self):
        report, _, unattributed, _, _ = self.run_on({"a.jsonl": [
            user("u1", "2026-01-04T10:00:00Z", "before the claim, on its branch"),
            user("u2", "2026-01-07T10:00:00Z", "after the merge"),
            user("u3", "2026-01-04T11:00:00Z", "before the claim, naming ABC-7 elsewhere", branch="main", session="m"),
        ]})
        self.assertEqual((report["ABC-7"]["prompt"], unattributed), (1, 2))

    def test_an_event_no_session_made_is_an_outside_touch(self):
        report, _, _, _, _ = self.run_on({"a.jsonl": [
            agent("a1", "2026-01-05T11:00:00Z", "gh pr comment 12 --body x"),
            agent("a2", "2026-01-05T12:00:00Z", tool="mcp__plugin_x_linear__save_issue"),
        ]}, events=[
            {"ticket": "ABC-7", "kind": "comment", "at": "2026-01-05T11:01:00Z"},
            {"ticket": "ABC-7", "kind": "state", "at": "2026-01-05T12:00:30Z"},
            {"ticket": "ABC-7", "kind": "state", "at": "2026-01-05T15:00:00Z"},
            {"ticket": "ABC-7", "kind": "branch deleted", "at": "2026-01-06T18:01:00Z"},
        ])
        self.assertEqual(report["ABC-7"]["outside"], 1)

    def test_reading_the_pr_does_not_explain_an_event(self):
        report, _, _, _, _ = self.run_on({"a.jsonl": [agent("a1", "2026-01-05T11:00:00Z", "gh pr view 12 --json state")]},
                                      events=[{"ticket": "ABC-7", "kind": "state", "at": "2026-01-05T11:00:30Z"}])
        self.assertEqual(report["ABC-7"]["outside"], 1)

    def test_a_failed_shell_merge_typed_again_is_one_shell_touch_and_the_merge(self):
        report, _, _, _, _ = self.run_on({"a.jsonl": [
            user("u1", "2026-01-06T17:58:00Z", "<bash-input>gh pr merge 12</bash-input>"),
            user("u2", "2026-01-06T17:59:50Z", "<bash-input>gh pr merge 12 --merge</bash-input>"),
        ]}, events=[{"ticket": "ABC-7", "kind": "merge", "at": "2026-01-06T18:00:00Z"}])
        self.assertEqual(report["ABC-7"], {"prompt": 0, "shell": 1, "outside": 0, "merge": 1})

    def test_the_prompt_that_asks_an_agent_to_merge_is_the_merge(self):
        report, _, _, _, _ = self.run_on({"a.jsonl": [
            user("u1", "2026-01-06T17:58:00Z", "merge it"),
            agent("a1", "2026-01-06T17:59:00Z", "gh pr merge 12 --merge"),
        ]}, events=[{"ticket": "ABC-7", "kind": "merge", "at": "2026-01-06T17:59:10Z"}])
        self.assertEqual(report["ABC-7"], {"prompt": 0, "shell": 0, "outside": 0, "merge": 1})

    def test_a_prompt_typed_while_the_agent_works_counts(self):
        queued = {"uuid": "q1", "type": "attachment", "timestamp": "2026-01-05T10:00:00Z",
                  "gitBranch": "abc-7-add", "cwd": "/repo", "sessionId": "s1", "isSidechain": False,
                  "attachment": {"type": "queued_command", "commandMode": "prompt", "humanTurn": True,
                                 "origin": {"kind": "human"}, "prompt": "also this", "usage": {"input_tokens": 7}}}
        notice = dict(queued, uuid="q2", attachment={"type": "queued_command", "commandMode": "task-notification",
                                                     "origin": {"kind": "task-notification"}, "prompt": "done"})
        report, _, _, _, _ = self.run_on({"a.jsonl": [queued, notice]})
        self.assertEqual(report["ABC-7"]["prompt"], 1)

    def test_the_agents_prose_and_command_output_name_nothing(self):
        prose = agent("a2", "2026-01-06T09:02:00Z", branch="HEAD", session="r")
        prose["message"]["content"] = [{"type": "text", "text": "color #333 on #fff, unlike PR 3"}]
        report, _, unattributed, _, _ = self.run_on({"r.jsonl": [
            agent("a1", "2026-01-06T09:01:00Z", "gh pr checkout 12 --detach", branch="HEAD", session="r"),
            prose,
            user("u1", "2026-01-06T09:03:00Z", "<bash-stdout>see #3</bash-stdout>", branch="HEAD", session="r"),
            user("u2", "2026-01-06T09:05:00Z", "looks right", branch="HEAD", session="r"),
        ]})
        self.assertEqual((report["ABC-7"]["prompt"], unattributed), (1, 0))

    def test_work_on_another_item_on_the_tickets_branch_is_not_the_tickets(self):
        report, _, unattributed, _, _ = self.run_on({"a.jsonl": [
            user("u1", "2026-01-05T10:00:00Z", "build it"),
            user("u2", "2026-01-05T11:00:00Z", "now trim #4 and close it"),
            user("u3", "2026-01-05T11:05:00Z", "and its worktree"),
            user("u4", "2026-01-05T12:00:00Z", "back to ABC-7"),
        ]})
        self.assertEqual((report["ABC-7"]["prompt"], unattributed), (2, 2))

    def test_the_build_sessions_prompts_before_the_claim_count(self):
        report, _, unattributed, _, _ = self.run_on({"a.jsonl": [
            user("u1", "2026-01-05T08:50:00Z", "start ABC-7"),
            user("u2", "2026-01-04T08:50:00Z", "on another branch before", branch="main"),
        ]})
        self.assertEqual((report["ABC-7"]["prompt"], unattributed), (1, 1))

    def test_an_agent_acting_on_another_ticket_does_not_explain_an_event(self):
        other = {"id": "ABC-8", "branch": "abc-8-", "pr": 13, "claimed": "2026-01-05T09:00:00Z",
                 "merged": "2026-01-06T18:00:00Z"}
        report, _, _, _, _ = self.run_on({"a.jsonl": [
            agent("a1", "2026-01-05T12:00:00Z", "gh pr comment 13 --body x", branch="abc-8-other", session="s8"),
        ]}, events=[{"ticket": "ABC-7", "kind": "state", "at": "2026-01-05T12:01:00Z"}], tickets=(TICKET, other))
        self.assertEqual(report["ABC-7"]["outside"], 1)

    def test_ids_with_a_digit_in_their_prefix(self):
        ticket = dict(TICKET, id="AB2-7", branch="never-matches")
        report, _, _, _, _ = self.run_on({"a.jsonl": [user("u1", "2026-01-05T10:00:00Z", "review AB2-7", branch="HEAD")]},
                                         tickets=(ticket,))
        self.assertEqual(report["AB2-7"]["prompt"], 1)

    def test_prints_counts_only(self):
        line = user("u1", "2026-01-05T10:00:00Z", SECRET)
        line["totalCostUSD"] = 12.34
        line["message"]["usage"] = {"input_tokens": 5555}
        directory = tempfile.mkdtemp()
        with open(os.path.join(directory, "a.jsonl"), "w", encoding="utf-8") as out:
            out.write(json.dumps(line) + "\n")
        config = os.path.join(directory, "tickets.json")
        with open(config, "w", encoding="utf-8") as out:
            json.dump({"tickets": [TICKET]}, out)
        printed = io.StringIO()
        argv = sys.argv
        sys.argv = ["touches.py", config, directory]
        try:
            with contextlib.redirect_stdout(printed):
                touches.main()
        finally:
            sys.argv = argv
        output = printed.getvalue()
        self.assertIn("| ABC-7 | 1 | 0 | 0 | 1 | 2 |", output)
        for leaked in (SECRET, "12.34", "5555"):
            self.assertNotIn(leaked, output)


if __name__ == "__main__":
    unittest.main()
