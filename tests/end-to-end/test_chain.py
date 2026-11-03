"""Unit tests for the end-to-end ticket's harness: the stub gh's writes, the reading of a session,
the judgement of a run and the page check. On invented data; no session runs.

Run: python3 -m unittest discover tests/end-to-end
"""
import argparse
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

# The page imports flow.py too, and must never run a stale cached copy of it (see build-workflow.py).
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
spec = importlib.util.spec_from_file_location("end_to_end_run", os.path.join(HERE, "run.py"))
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)

import page_check

GIT = {**os.environ, **run.routing.GIT}
# A page that meets the ticket, in the fixture's own shape, for the check to read.
SERVER = '''
import html, json, os, re, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs

STORE = Path(os.environ["PANTRY_STORE"])


def load():
    return json.loads(STORE.read_text()) if STORE.exists() else {}


def page(message="", typed=""):
    items = load()
    rows = "".join(f"<li>{html.escape(name)} {quantity}</li>" for name, quantity in items.items())
    return (f"<h1>Pantry</h1><ul>{rows or 'Nothing in the pantry yet.'}</ul><p>{message}</p>"
            '<form action="/items" method="post"><label>Item <input name="name"></label>'
            f'<label>Quantity <input name="quantity" value="{typed}"></label><button>Add</button></form>')


class Page(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def answer(self, text):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(text.encode())

    def do_GET(self):
        self.answer(page())

    def do_POST(self):
        form = parse_qs(self.rfile.read(int(self.headers["Content-Length"])).decode())
        name, quantity = form.get("name", [""])[0], form.get("quantity", [""])[0]
        if not name:
            return self.answer(page("Give the item a name.", quantity))
        items = load()
        amount, unit = re.fullmatch(r"(\\d+)(\\D+)", quantity).groups()
        if name in items:
            held, held_unit = re.fullmatch(r"(\\d+)(\\D+)", items[name]).groups()
            if held_unit != unit:
                return self.answer(page("Use the same unit as before.", quantity))
            amount = str(int(held) + int(amount))
        items[name] = amount + unit
        STORE.write_text(json.dumps(items))
        self.answer(page())


if sys.argv[1:2] == ["serve"]:
    HTTPServer(("127.0.0.1", int(sys.argv[2])), Page).serve_forever()
'''


class Project(unittest.TestCase):
    """A git repo with a local origin, gh being the stub, and one pushed branch."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="test-chain-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.where = os.path.join(self.root, "project")
        os.makedirs(self.where)
        self.git("init", "-q", "-b", "main")
        self.write("a.txt", "one\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "Start")
        self.git("init", "-q", "--bare", "-b", "main", os.path.join(self.root, "origin.git"))
        self.git("remote", "add", "origin", os.path.join(self.root, "origin.git"))
        self.git("push", "-q", "origin", "main")
        self.git("switch", "-q", "-c", "5-a-thing")
        self.write("a.txt", "two\n")
        self.git("commit", "-q", "-am", "Change the thing")
        self.write_state([])

    def write(self, name, text):
        with open(os.path.join(self.where, name), "w", encoding="utf-8") as out:
            out.write(text)

    def write_state(self, listed):
        with open(os.path.join(self.where, ".git", "fixture-prs.json"), "w", encoding="utf-8") as out:
            json.dump(listed, out)

    def git(self, *arguments):
        return subprocess.run(["git", *arguments], cwd=self.where, env=GIT, check=True, capture_output=True, text=True).stdout

    def gh(self, *arguments, ok=True):
        done = subprocess.run([os.path.join(run.routing.STUB, "gh"), *arguments], cwd=self.where, capture_output=True, text=True)
        if ok:
            self.assertEqual(done.returncode, 0, done.stderr)
        return done

    def opened(self):
        self.git("push", "-q", "origin", "5-a-thing")
        self.gh("pr", "create", "--title", "A thing", "--body", "Ticket: #5")
        return json.loads(self.gh("pr", "view", "12", "--json", "number,title,body,files,headRefOid,commits,comments,reviews").stdout)


class StubCreates(Project):
    def test_a_branch_that_was_not_pushed_has_no_pull_request(self):
        done = self.gh("pr", "create", "--title", "A thing", ok=False)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("git push -u origin 5-a-thing", done.stderr)

    def test_a_pushed_branch_opens_one_with_git_s_facts(self):
        pr = self.opened()
        self.assertEqual((pr["number"], pr["title"], pr["body"]), (12, "A thing", "Ticket: #5"))
        self.assertEqual(pr["files"], [{"path": "a.txt"}])
        self.assertEqual(pr["headRefOid"], self.git("rev-parse", "HEAD").strip())
        self.assertEqual([commit["messageHeadline"] for commit in pr["commits"]], ["Change the thing"])

    def test_a_body_may_come_from_a_file(self):
        self.git("push", "-q", "origin", "5-a-thing")
        self.write("body.md", "From a file")
        self.gh("pr", "create", "--title", "A thing", "--body-file", "body.md")
        self.assertEqual(json.loads(self.gh("pr", "view", "12", "--json", "body").stdout)["body"], "From a file")

    def test_a_branch_has_one_open_pull_request(self):
        self.opened()
        self.assertNotEqual(self.gh("pr", "create", "--title", "Again", ok=False).returncode, 0)

    def test_its_diff_is_git_s(self):
        self.opened()
        self.assertIn("+two", self.gh("pr", "diff", "12").stdout)
        self.assertEqual(self.gh("pr", "diff", "12", "--name-only").stdout.strip(), "a.txt")


class StubWrites(Project):
    def setUp(self):
        super().setUp()
        self.opened()

    def view(self, *fields):
        return json.loads(self.gh("pr", "view", "12", "--json", ",".join(fields)).stdout)

    def test_a_comment_lands_with_its_options_first(self):
        self.gh("pr", "comment", "--body", "A finding", "12")
        self.assertEqual(self.view("comments")["comments"][0]["body"], "A finding")

    def test_a_review_comment_lands(self):
        self.gh("pr", "review", "12", "--comment", "--body", "Findings")
        self.assertEqual(self.view("reviews")["reviews"][0]["state"], "COMMENTED")

    def test_the_author_cannot_approve_or_request_changes(self):
        for flag in ("--approve", "--request-changes"):
            done = self.gh("pr", "review", "12", flag, "--body", "No", ok=False)
            self.assertNotEqual(done.returncode, 0)
            self.assertIn("your own pull request", done.stderr)

    def test_an_edit_keeps_what_it_does_not_name(self):
        self.gh("pr", "edit", "12", "--title", "A better thing")
        pr = self.view("title", "body")
        self.assertEqual((pr["title"], pr["body"]), ("A better thing", "Ticket: #5"))

    def test_a_detached_checkout_lands_on_the_pushed_head(self):
        head = self.git("rev-parse", "HEAD").strip()
        self.git("switch", "-q", "main")
        self.gh("pr", "checkout", "12", "--detach")
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), head)
        self.assertEqual(self.git("branch", "--show-current").strip(), "")

    def test_the_merge_and_everything_else_are_refused(self):
        for command in (["pr", "merge", "12"], ["api", "repos/owner/pantry"], ["pr", "close", "12"]):
            self.assertNotEqual(self.gh(*command, ok=False).returncode, 0, command)


class StubReads(Project):
    def test_a_scenario_s_files_still_read_as_written(self):
        self.write_state([{"number": 12, "title": "T", "headRefName": "unpushed", "files": [{"path": "b.py"}]}])
        self.assertIn("diff --git a/b.py b/b.py", self.gh("pr", "diff", "12").stdout)


class Finished(Project):
    def test_no_pull_request_is_not_finished(self):
        self.assertFalse(run.finished(self.where))

    def test_an_open_pull_request_with_everything_pushed_is(self):
        self.opened()
        self.assertTrue(run.finished(self.where))

    def test_a_change_not_committed_keeps_the_build_going(self):
        self.opened()
        self.write("a.txt", "three\n")
        self.assertFalse(run.finished(self.where))

    def test_a_commit_not_pushed_keeps_the_build_going(self):
        self.opened()
        self.write("a.txt", "three\n")
        self.git("commit", "-q", "-am", "One more")
        self.assertFalse(run.finished(self.where))

    def test_a_new_file_left_aside_does_not(self):
        self.opened()
        self.write("scratch.txt", "notes\n")
        self.assertTrue(run.finished(self.where))


class Printed(unittest.TestCase):
    def test_the_code_review_carries_its_arguments(self):
        line = run.printed("/code-review-and-quality", PR=12)
        self.assertTrue(line.startswith("/code-review-and-quality 12. "), line)
        self.assertIn("Post the findings on the PR.", line)

    def test_the_acceptance_review_names_the_pull_request_and_the_ticket(self):
        self.assertTrue(run.printed("/acceptance-review", PR=12, ticket=5).startswith("/acceptance-review 12 against 5."))


class ReadSession(unittest.TestCase):
    EVENTS = [
        "not json",
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "Reading."},
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/home/x/.claude/skills/tdd/SKILL.md"}},
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/tmp/p/docs/interface/1-walking-skeleton.md"}},
            {"type": "tool_use", "name": "Skill", "input": {"skill": "lesson-learned"}},
            {"type": "tool_use", "name": "Bash", "input": {"command": "cat CODING_STANDARDS.md"}}]}},
        {"type": "result", "result": "Done.", "session_id": "s1", "num_turns": 4, "total_cost_usd": 1.5,
         "permission_denials": [{"tool_name": "Bash"}], "is_error": False, "subtype": "success"}]

    def setUp(self):
        self.found = run.read_session([event if isinstance(event, str) else json.dumps(event) for event in self.EVENTS])

    def test_it_reads_the_result(self):
        found = self.found
        self.assertEqual((found["answer"], found["id"], found["turns"], found["cost"], found["error"]), ("Done.", "s1", 4, 1.5, None))
        self.assertEqual(len(found["denied"]), 1)

    def test_a_skill_loaded_or_read_from_disk_counts(self):
        self.assertEqual(self.found["skills"], ["tdd", "lesson-learned"])

    def test_a_skill_read_by_a_command_counts(self):
        command = "cat ~/.claude/skills/incremental-implementation/SKILL.md ~/.claude/skills/test-driven-development/SKILL.md"
        event = {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": command}},
            {"type": "tool_use", "name": "Bash", "input": {"command": "grep -n Done skills/tdd/SKILL.md.bak"}}]}}
        self.assertEqual(run.read_session([json.dumps(event)])["skills"], ["incremental-implementation", "test-driven-development"])

    def test_a_document_counts_as_read_by_a_read_or_a_command(self):
        self.assertEqual(run.documents_read(self.found), ["interface design", "coding standards"])

    def test_an_error_is_kept(self):
        line = json.dumps({"type": "result", "is_error": True, "subtype": "error_max_turns"})
        self.assertEqual(run.read_session([line])["error"], "error_max_turns")

    def test_replies_add_up_and_the_last_answer_stands(self):
        total = run.add(dict(self.found, skills=list(self.found["skills"])), dict(self.found, answer="Later.", id=None, skills=["pair"]))
        self.assertEqual((total["cost"], total["turns"], total["answer"], total["id"]), (3.0, 8, "Later.", "s1"))
        self.assertEqual(total["skills"], ["tdd", "lesson-learned", "pair"])


class ReviewWord(unittest.TestCase):
    def test_the_first_word_stands(self):
        self.assertEqual(run.review_word("Verdict: **Request changes**, or I would approve."), "request changes")

    def test_an_approval_reads_as_one(self):
        self.assertEqual(run.review_word("I approve this."), "approve")

    def test_the_review_s_other_ways_of_saying_it_count(self):
        self.assertEqual(run.review_word("**Verdict: changes needed.**"), "changes needed")
        self.assertEqual(run.review_word("Approved, with one nit."), "approved")

    def test_a_review_may_say_neither(self):
        self.assertIsNone(run.review_word("Some findings."))


class Judge(unittest.TestCase):
    STEP = dict(run.read_session([]), answer="Answered.")
    GOOD = {"replies": 4, "finished": True, "number": 12, "branch": "5-add-from-the-page", "body": "Ticket: #5", "commits": ["One"], "attributed": [],
            "ci": {"pytest": True, "mypy": True}, "page": {"contract": {"form": True}, "design": {"button Add": False}, "escapes": False},
            "status pushed": "in review", "status in the folder": "started", "checkout": True, "verdict": "satisfies", "posted": 1,
            "main moved": False, "steps": {"build": STEP, "code review": STEP, "security review": STEP, "acceptance review": STEP}}

    def failing(self, **changes):
        return run.judge({**copy.deepcopy(self.GOOD), **changes})

    def test_a_sound_chain_passes_whatever_the_recorded_facts_say(self):
        self.assertEqual(self.failing(), [])

    def test_no_pull_request_stops_the_judgement_there(self):
        self.assertEqual(run.judge({"steps": {"build": self.STEP}, "replies": 12}), ["the build opened no pull request after 12 replies"])

    def test_each_fault_is_named(self):
        faults = {"CI failed: mypy": {"ci": {"mypy": False}},
                  "the page fails the ticket: form": {"page": {"contract": {"form": False}}},
                  "the build left work unpushed after 4 replies": {"finished": False},
                  "a commit carries an attribution: One": {"attributed": ["One"]},
                  "main moved: no step may merge": {"main moved": True},
                  "branch other is not named after the ticket": {"branch": "other"},
                  "the pull request does not link its ticket": {"body": "Nothing"},
                  "the ticket did not move to in review": {"status pushed": "open", "status in the folder": "open"},
                  "the code review posted nothing on the pull request": {"posted": 0},
                  "the acceptance review printed no verdict": {"verdict": None}}
        for failure, change in faults.items():
            self.assertIn(failure, self.failing(**change))

    def test_a_requested_rework_on_a_sound_build_is_the_chain_s_answer(self):
        self.assertEqual(self.failing(verdict="does-not-satisfy"), [])

    def test_a_pass_on_a_broken_page_fails_the_run(self):
        self.assertIn("the acceptance review passed a ticket that fails its own check",
                      self.failing(page={"contract": {"form": False}}))

    def test_a_session_s_error_is_named(self):
        steps = {**self.GOOD["steps"], "code review": dict(self.STEP, error="error_max_turns")}
        self.assertIn("code review: error_max_turns", self.failing(steps=steps))


class Report(unittest.TestCase):
    def test_it_names_what_a_reader_compares_between_runs(self):
        root = tempfile.mkdtemp(prefix="test-report-")
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        facts = {**copy.deepcopy(Judge.GOOD), "review says": "changes requested", "body attributed": False}
        facts["page"]["idle"] = False
        args = argparse.Namespace(model="a-model", effort="medium")
        path = os.path.join(root, "report.md")
        run.report(facts, [], {"sha": "0123456789", "dirty": False}, args, 3.0, path)
        with open(path, encoding="utf-8") as file:
            text = file.read()
        for words in ("# End-to-end ticket: passed", "`0123456`", "touches in the build: 4", "saying `changes requested`",
                      "| build | 0 |", "answers beside an idle connection | no |", "<summary>code review"):
            self.assertIn(words, text)


class PageCheck(unittest.TestCase):
    def check(self, server=SERVER):
        root = tempfile.mkdtemp(prefix="test-page-")
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        os.makedirs(os.path.join(root, "src"))
        with open(os.path.join(root, "src", "pantry.py"), "w", encoding="utf-8") as out:
            out.write(server)
        return page_check.check(root, os.path.join(root, "store.json"))

    def test_a_page_that_meets_the_ticket_passes_every_criterion(self):
        facts = self.check()
        self.assertEqual({name: ok for name, ok in facts["contract"].items() if not ok}, {})
        self.assertEqual(len(facts["contract"]), 6)

    def test_it_reads_the_design_and_the_escaping_apart_from_the_ticket(self):
        facts = self.check()
        self.assertEqual({name: ok for name, ok in facts["design"].items() if not ok}, {})
        self.assertTrue(facts["escapes"])

    def test_a_page_that_does_not_add_up_fails_that_criterion_alone(self):
        facts = self.check(SERVER.replace("amount = str(int(held) + int(amount))", "amount = held"))
        self.assertEqual([name for name, ok in facts["contract"].items() if not ok], ["adds up", "refuses another unit"])

    def test_an_unescaped_name_is_recorded_but_stays_out_of_the_ticket(self):
        facts = self.check(SERVER.replace("html.escape(name)", "name"))
        self.assertFalse(facts["escapes"])
        self.assertTrue(all(facts["contract"].values()))

    def test_a_design_left_out_is_recorded_but_stays_out_of_the_ticket(self):
        facts = self.check(SERVER.replace("<h1>Pantry</h1>", "").replace("<label>Item ", "").replace("</label>", ""))
        self.assertFalse(facts["design"]["heading Pantry"])
        self.assertTrue(all(facts["contract"].values()))

    def test_a_one_thread_server_hangs_beside_an_idle_connection(self):
        facts = self.check()
        self.assertFalse(facts["idle"])
        self.assertTrue(all(facts["contract"].values()))

    def test_a_threaded_server_answers_beside_one(self):
        server = SERVER.replace("BaseHTTPRequestHandler, HTTPServer", "BaseHTTPRequestHandler, ThreadingHTTPServer")
        self.assertTrue(self.check(server.replace("HTTPServer((", "ThreadingHTTPServer(("))["idle"])

    def test_a_page_that_never_serves_fails(self):
        self.assertEqual(self.check("import sys\nsys.exit(1)\n")["contract"], {"serves the page": False})


class Fixture(unittest.TestCase):
    def test_the_project_starts_clean_and_pushed_with_the_ticket_open(self):
        where = tempfile.mkdtemp(prefix="test-fixture-")
        self.addCleanup(shutil.rmtree, where, ignore_errors=True)
        self.addCleanup(shutil.rmtree, where + ".origin.git", ignore_errors=True)
        base = run.build_project(where, GIT)
        self.assertEqual(subprocess.run(["git", "rev-parse", "origin/HEAD"], cwd=where, capture_output=True, text=True).stdout.strip(), base)
        self.assertEqual(run.ticket_status(run.ticket_file(where)), "open")
        self.assertTrue(os.path.exists(os.path.join(where, "docs", "interface", "1-walking-skeleton.md")))
        self.assertTrue(os.path.exists(os.path.join(where, "CLAUDE.md")))
        self.assertEqual(run.open_prs(where), [])

    def test_the_acceptance_criteria_the_page_check_reads_are_the_ticket_s(self):
        with open(os.path.join(run.ROOT, "tests", "routing", "layers", "screen", "issues", "5-store-a-new-item.md"), encoding="utf-8") as file:
            ticket = file.read()
        for words in (page_check.EMPTY, page_check.OTHER_UNIT, page_check.NO_NAME):
            self.assertIn(words, ticket)


if __name__ == "__main__":
    unittest.main()
