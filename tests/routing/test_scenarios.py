"""Unit tests for what the routing scenarios check, run offline: no session, no cost.

The ticket breakdown is confirmed in the session that runs /to-tickets; no gate waits on an
approval of the tickets. Four scenarios fail an answer that still reports one, with the check
'old ticket gate' in checks.py. It is tested here against wordings of the old gate, most from
answers the router gave before the change, and of the confirmation.

Run: python3 -m unittest discover tests/routing
"""
import json
import os
import re
import sys
import time
import unittest
import unittest.mock

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import checks
import run

TICKET_GATE = {"check": "old ticket gate"}
# Each scenario, and whether its light answer is checked too: only a step 10 light answer names its gate.
TICKET_GATE_SCENARIOS = {"refined-stories-to-tickets": True, "sized-bounded-issue": True,
                         "design-approved-stories-unrefined": False, "fits-an-open-epic": False}

# Wordings of the old gate, most from answers the router gave before the change.
OLD = [
    "**Gate:** you approve the tickets before they are published.",
    "**Gate:** you approve the ticket before `/to-tickets` publishes it to `issues/`.",
    "**Gate:** you approve the tickets, and they count as approved once they are published to `issues/`.",
    "**Gate:** step 9 has none. At step 10 you approve the tickets before they are published.",
    "**Gate:** none at refinement. The next gate is the tickets, which you approve before `/to-tickets` publishes them.",
    "**Gate:** none. Triage sets the issue's state; tickets get approved later, when they are published",
    "**Gate:** tickets approved before publishing.",
    "**Gate:** nothing is built until you approve the tickets.",
    "**Gate:** the tickets are not published until you approve them.",
    "**Gate:** nothing publishes without your approval of the tickets.",
    "**Gate:** none until you approve the tickets.",
    "**Gate:** none, but the tickets wait for your approval.",
    "**Gate:** the tickets need your approval before step 11.",
    "**Gate:** tickets need approval.",
    "**Gate:** tickets must be approved before step 11.",
    "**Gate:** you sign off the tickets before they are built.",
    "**Gate:** you approve the tickets rather than the plan.",
    "**Gate:** step 10 is gated.",
    "**Gate:** the ticket approval gate.",
    "**Step 10, Tickets** · architect session · gate: you approve the tickets before they're published",
    "**Step 10, Tickets** · architect per epic (same session as refinement when it fits) · gate: tickets approved before publishing",
    "**Step 10, Tickets** · architect · tickets approved before publishing",
    "**After that:**\n1. Step 9, `/specification #5`, then `/find-gaps`. No gate.\n"
    "2. Step 10, same session: `/to-tickets #1`. Gate: you approve the tickets before they are published.",
    "**After that:**\n- **Step 10:** run `/to-tickets 1`. It leaves tickets with blocking edges. Gate: you approve them before they're published.",
    "**After that:** a bounded fix goes to `/to-tickets <issue>` (gate: you approve the tickets before they are published), "
    "then `/build-ticket <ticket>` in a developer session.",
    "**After that:** `/to-tickets #1`, which leaves tickets with blocking edges; publishing them is the approval.",
    "**After that:** `/to-tickets <story>`. It leaves tickets with blocking edges, approved by publishing.",
    "**After that:** step 10, `/to-tickets 1` makes tickets with blocking edges, and they are approved when you publish.",
    "**Gate:** none for refinement. At step 10, publishing the tickets is what approves them.",
    "**After that:** if it fits one ticket, `/to-tickets <issue>` publishes the ticket (gate: you approve it before it's published).",
    # Other wordings: half-updated answers that add the confirmation and keep the gate, and phrasings
    # the router has not used yet.
    "**Gate:** you confirm the breakdown, and the tickets are approved before they are published.",
    "**Gate:** you confirm the breakdown, then the tickets wait for your approval before step 11.",
    "**Gate:** you approve the tickets before they are published, and confirm the order.",
    "**Gate:** you okay the tickets before they are published.",
    "**Gate:** your approval of the tickets.",
    "**Gate:** you sign off on the tickets.",
    "**Gate:** the tickets go to you for approval before they are published.",
    "**Gate:** the tickets are not published until approved.",
    "**Gate:** none. The tickets publish pending your approval.",
    "**Gate:** none.\n**Step 10:** you approve the tickets before they are published.",
    "**Step 10, Tickets** · architect · gate: you approve them before publishing",
    "**After that:**\n- Step 10: `/to-tickets 1`, gated on your approval.",
    "**After that:** step 10, `/to-tickets 2` (approval gate), then step 11.",
    # An adjective between the determiner and the tickets, or "after" as the condition.
    "**Gate:** you approve the new tickets before they are published.",
    "**Gate:** you approve the generated tickets before they publish.",
    "**Gate:** you approve the three tickets before they publish.",
    "**Gate:** approval of the published tickets.",
    "**Gate:** the tickets publish after you approve them.",
    "**Gate:** the tickets publish only after your approval.",
    "**Gate:** the tickets go live after your approval.",
    "**After that:** step 10, `/to-tickets 1`, then step 11. Step 13: you merge.\n"
    "Step 10's tickets publish after you approve them.",
    # The session named in a sentence of its own, as where step 10 runs, does not clear the approval.
    "**After that:**\n4. **Step 10, tickets**: `/to-tickets <story>`, in the same session as step 9. "
    "Gate: you approve the tickets before they are published.",
    "**After that:** `/specification 3`, then `/to-tickets 1` in the same session as `/specification`; "
    "the tickets count as approved once published.",
    # A single ticket, "it" for the ticket, and the tickets waiting in other words.
    "**Gate:** `/to-tickets` publishes the ticket once you approve it.",
    "**After that:** a bounded fix goes to `/to-tickets <issue>`, which publishes the ticket once you approve it.",
    "**After that:** `/to-tickets 3` leaves a ticket for that criterion, published once you approve it.",
    "**After that:**\n1. `/to-tickets <issue>` in an architect session writes the ticket. You approve it before it's published.",
    "**Gate:** the tickets are published only with your approval.",
    "**Gate:** the tickets wait for you to approve them.",
    "**Gate:** Once you approve it, the ticket is published.",
    "**Gate:** Once you approve them, the tickets publish.",
    "**After that:** when you approve them, the tickets go to the tracker.",
    "**After that:** `/to-tickets 1` drafts the tickets. Once you approve them, step 11 starts.",
    "**After that:** `/to-tickets 1` drafts the tickets. Once you approve them, `/build-ticket` picks each up.",
    "**After that:** `/to-tickets 1` drafts the tickets; after you approve them, `/build-ticket 12`.",
    "**After that:** `/to-tickets 1` drafts the tickets. When you approve them, they go to the tracker and `/build-ticket` starts.",
    "**Gate:** the tickets need your OK before they publish.",
    "**Gate:** the tickets need your go-ahead before they are published.",
    "**Gate:** you accept the tickets before they are published.",
    "**Gate:** you review and approve the tickets before they are published.",
    "**Gate:** no gate: you approve the tickets before they publish.",
    "**Gate:** none except your approval of the tickets.",
    "**Gate:** nothing besides your approval of the tickets.",
    "**Gate:** nothing other than approving the tickets.",
    # A session named as the role, or in another sentence, is not the confirmation.
    "**After that:** add a ticket with `/to-tickets 3` (architect session, approved by publishing).",
    "**After that:** Step 10 runs in the same session: `/to-tickets 1`, and you approve the tickets.",
    # The tickets qualified by what they come from: the stories, the epic, the PRD.
    "**After that:** `/find-gaps` on #5 (no gate), which leaves #5 refined. Then step 10, `/to-tickets #1`: tickets for "
    "stories #3, #4 and #5 with blocking edges, approved by you before they are published. Then step 11 in a developer "
    "session, `/build-ticket <ticket>` per ticket.",
    "**Gate:** the tickets for epic #1 are approved before they're published.",
    "**Gate:** the tickets for story #3 are approved before they are published.",
    "**Gate:** the tickets of each story need your approval before they publish.",
    "**Gate:** the tickets, one per story, need your approval before they publish.",
    "**Gate:** tickets for the stories, approved before publishing.",
    "**Gate:** the tickets from the PRD's stories are approved before publishing.",
    # After that is read past step 10.
    "**After that:** `/to-tickets <issue>`, then `/build-ticket <ticket>`. You approve the tickets by publishing them.",
]
# Wordings of the confirmation, and other lines the check must leave alone: an approval of the
# breakdown is the confirmation, and approvals of the PRD or of a PR are other steps.
NEW = [
    "**Gate:** none. You confirm the breakdown in the same session, then the tickets publish.",
    "**Gate:** nothing to approve. You confirm the ticket breakdown in that same session, and the ticket is then written to `issues/`.",
    "**Gate:** none. `/to-tickets` shows you the breakdown, you confirm it in that same session, and then the ticket is published.",
    "**Gate:** you approve the breakdown in this session.",
    "**After that:** once you approve it, the PRD gets its stories.",
    "**Gate:** when you confirm it in this session, the tickets publish.",
    "**Gate:** you approve the breakdown in the session, then the tickets are published.",
    "**Gate:** no separate gate; you approve the breakdown in that session, then it publishes.",
    "**Gate:** none. You approve the breakdown in the same session, then the tickets publish.",
    "**Gate:** none; `/to-tickets` asks you to approve the breakdown in its session before it publishes.",
    "**Gate:** a confirmation, not a gate: you approve the breakdown when /to-tickets shows it.",
    "**Gate:** confirmation in session; tickets publish once you approve the breakdown in it.",
    "**Gate:** none; the tickets publish with nothing waiting on an approval.",
    "**Gate:** none. The tickets need no approval.",
    "**Gate:** none: there is no separate ticket approval.",
    "**Gate:** none. The tickets don't wait for an approval.",
    "**Gate:** none. You don't need to approve the tickets separately.",
    "**Gate:** none; nothing to approve before the tickets publish.",
    "**Gate:** none. Step 10 has no gate.",
    "**Gate:** none. The design doc is already approved, so the tickets come next.",
    "**Gate:** you approve the PRD again before stories and tickets are made.",
    "**Step 10, Tickets** · architect session for epic #1 · no gate: you confirm the breakdown in the same session, then the tickets publish",
    "**Step 10, Tickets** · architect per epic, in the same session as refinement if there's room · no gate: you confirm the breakdown in that session",
    "**Step 10, Tickets** · architect for epic #1 · no gate (you confirm the breakdown in the same session)",
    "**Step 10, Tickets** · architect · no gate",
    "**After that:** for epic #2, after its PRD is approved: `/technical-writing`, then `/writing-design-docs 2`, "
    "then `/specification <story>` and `/to-tickets 2`.",
    "**After that:** step 10, `/to-tickets 1`, where you confirm the breakdown; then step 11, `/build-ticket <ticket>`. "
    "Step 13: you merge once the review approves.",
    "**After that:**\n2. Step 10, same session: `/to-tickets #1`. No gate: you confirm the breakdown there, then the tickets publish.",
    "**Gate:** none. `/to-tickets` iterates until you approve the breakdown, then publishes.",
    "**Gate:** none. You approve the breakdown there, then the tickets publish.",
    "**Gate:** none; you approve the breakdown when `/to-tickets` shows it.",
    "**Gate:** none. You approve the breakdown in the architect session, then the tickets publish.",
    "**Gate:** none. The tickets publish as soon as you approve the breakdown in the session.",
    "**Gate:** none. The tickets publish as you approve the breakdown.",
    "**Gate:** you approve the breakdown before `/to-tickets` publishes it.",
    "**Gate:** you approve the ticket breakdown before it is published.",
    "**Gate:** you approve the tickets in this session, then they publish.",
    "**Gate:** no ticket is built before you approve the breakdown.",
    "**Gate:** no tickets publish until you approve the breakdown.",
    "**Gate:** the breakdown waits for your approval.",
    "**Gate:** you approve the PRD again before it is broken into stories and tickets.",
    "**Gate:** you approve the updated PRD; the tickets come later with no gate of their own.",
    "**Step 10, Tickets** · architect · no gate: you approve the breakdown as /to-tickets shows it",
    "**Step 10, Tickets** · architect, same session · no gate: approve the breakdown there",
    "**After that:** `/deliver-prd 1` again; once approved, the epic's stories are refined and broken into tickets.",
    "**After that:** once the PRD is approved, step 9 refines each story and step 10 breaks it into tickets.",
    "**After that:**\n1. Step 7, `/writing-design-docs 1`. Gate: you approve the design doc before stories are refined "
    "and tickets built.",
    "**After that:** for epic #2: once you approve its PRD, it has stories in the tracker. Then `/writing-design-docs 2` "
    "(approval gate), then `/specification <story>` and `/to-tickets 2`.",
    "**After that:** step 10, `/to-tickets 1`, which needs no approval gate.",
    "**After that:** step 10 is not gated: `/to-tickets 1` publishes once you confirm the breakdown.",
    "**After that:** step 12: the review approves the ticket's PR before step 13.",
    "**After that:** step 10, `/to-tickets 1`. Then each ticket is built, reviewed and approved before merge.",
    "**After that:** step 13: each ticket's PR is merged once the review approves it.",
    # After that goes on to the later steps and their own approvals: the review's and the merge's.
    "**After that:** Step 13, Merge: once the review approves the ticket, you merge.",
    "**After that:** Step 12: the reviewer approves each ticket or sends it back.",
    "**After that:** Step 13: you merge each ticket once approved.",
    "**After that:** Step 13: you merge the tickets once approved by review.",
    "**After that:** step 10, `/to-tickets 1`. Step 12: the reviewer approves each ticket or sends it back. "
    "Step 13: you merge the tickets once approved by review.",
    "**After that:** step 10, `/to-tickets 1`, then you merge each ticket once approved.",
    # "Approved" before a noun is another step's approval.
    "**After that:** step 10 makes tickets from the approved stories, and you confirm the breakdown in that session.",
    "**After that:** once the PRD is approved again, the story gets refined and its tickets follow the approved design.",
    "**After that:** step 10, `/to-tickets 1`; each ticket gets an approved review, then you merge it.",
    "**Step 10, Tickets.** The tickets follow from the approved design doc and the refined stories.",
    # Another step's gate after step 10's command.
    "**After that:** `/to-tickets 1`, then `/deliver-prd 2` (approval gate).",
    "**After that:** step 10 (`/to-tickets 1`), then epic #2's PRD (gated).",
    "**After that:** step 10, then step 12's approval gate on each PR.",
    "**After that:** `/to-tickets 1`, then step 13, gated on the review.",
    "**After that:** step 10, then step 6 for the next epic (approval gate).",
    "**After that:** `/to-tickets 1`; then epic #2 starts at step 6 with `/deliver-prd 2` (approval gate).",
    # The approved tickets /to-tickets publishes, as its own steps say.
    "**Gate:** none. You confirm the breakdown in this session; `/to-tickets` then publishes the approved tickets.",
    "**Gate:** none. `/to-tickets` iterates until you approve the breakdown, then publishes the approved tickets.",
    "**Step 10, Tickets** · architect · no gate: you confirm the breakdown, then the approved tickets publish",
    # The confirmation set in the session, in any word order.
    "**Gate:** you approve the tickets before they publish, in the same session.",
    "**Gate:** none. In the same session you approve the tickets, then they publish.",
    "**Gate:** none. In this session you approve the tickets, then `/to-tickets` publishes them.",
    "**Gate:** none. You approve the tickets in the architect session, then they publish.",
    "**Gate:** none. You approve the tickets right there in the session, then they publish.",
    "**Gate:** none. You approve the tickets in-session, then they publish.",
    "**Gate:** none. You approve the tickets there, in the same session.",
    "**Gate:** none. The tickets, once approved in this session, publish.",
    "**Gate:** none. You approve the tickets in the `/to-tickets` session, then they publish.",
    "**Gate:** none. You approve the tickets in `/to-tickets`'s session, then they publish.",
    "**Gate:** none: you approve the tickets (in the same session) before they publish.",
    "**Gate:** none. The tickets are confirmed (approved) in the same session.",
    "**Gate:** none. You approve the tickets as part of the same session, then they publish.",
    "**Gate:** none. You approve the tickets in the very same architect session.",
    "**Gate:** none; your approval of the tickets is part of the session.",
    # The breakdown, possessive.
    "**Gate:** none. You approve the tickets' breakdown, then they publish.",
    "**Gate:** none. You approve the ticket's breakdown, then it publishes.",
    # Other negations, and the review's approvals in other words.
    "**Gate:** none. The tickets publish without waiting for approval.",
    "**Gate:** you confirm the breakdown instead of approving the tickets.",
    "**Gate:** none. The tickets publish once the breakdown is approved.",
    "**After that:** step 10, `/to-tickets 1`, then each ticket gets its PR approved in review.",
    "**After that:** step 10, `/to-tickets 1`, and the tickets are approved through review once built.",
    "**Gate:** none. The tickets are approved later, at review, one PR at a time.",
    "**After that:** step 10, `/to-tickets 1`. Then build the tickets; acceptance approves each against its ticket.",
    "**After that:** Run: none, you approve or change the PRD at `docs/prd/1.md` first, then `/to-tickets 1`.",
]


def scenario(name):
    with open(os.path.join(HERE, "scenarios", name + ".json"), encoding="utf-8") as file:
        return json.load(file)


class TicketGate(unittest.TestCase):
    def test_old_gate_wordings_fail(self):
        for line in OLD:
            with self.subTest(line=line):
                self.assertTrue(checks.old_ticket_gate(line))

    def test_confirmation_wordings_pass(self):
        for line in NEW:
            with self.subTest(line=line):
                self.assertIsNone(checks.old_ticket_gate(line))

    def test_it_names_the_sentence(self):
        self.assertEqual(checks.old_ticket_gate("**Gate:** none. The tickets wait for your approval.\n"),
                         "The tickets wait for your approval")

    def test_scenarios_carry_the_check(self):
        for name, light in TICKET_GATE_SCENARIOS.items():
            with self.subTest(scenario=name):
                found = scenario(name)
                self.assertIn(TICKET_GATE, found.get("must_not", []))
                self.assertEqual(TICKET_GATE in found.get("light_must_not", []), light)

    def test_only_the_gate_parts_are_read(self):
        """The state table and the other lines are not read; After that stops at the next bold label."""
        answer = ("| 10 Tickets | `issues/` | none | you approve the tickets |\n"
                  "Why: you approve the tickets before they publish.\n**Gate:** none.\n\n**Next**\n```\n/to-tickets 1\n```\n"
                  "**After that:** step 11.\n\n---\n\nYou approve the tickets before they are published.\n")
        self.assertIsNone(checks.old_ticket_gate(answer))

    def test_long_answer_is_read_quickly(self):
        """A slow check would stall a paid run."""
        answer = ("**After that:** " + "step 10, `/to-tickets 1`, which publishes the tickets, then step 11. " * 500
                  + "\n" + "   - item, and its note\n" * 2000)
        started = time.monotonic()
        self.assertIsNone(checks.old_ticket_gate(answer))
        self.assertTrue(checks.old_ticket_gate(answer + "You approve the tickets before they are published.\n"))
        self.assertLess(time.monotonic() - started, 1)

    def test_light_answer_lines_are_read(self):
        """The light answer has no Gate line: its step 10 line carries the gate."""
        self.assertTrue(checks.old_ticket_gate("Done up to step 9: stories refined.\n**Step 10, Tickets** · architect · "
                                               "gate: you approve the tickets before they are published\n"))


class Light(unittest.TestCase):
    def test_light_run_keeps_only_its_own_checks(self):
        found = run.light({"layers": ["base"], "next": "^/full", "must": ["a"], "must_not": ["b"],
                           "light": "^/light", "light_must_not": ["c"]})
        self.assertEqual(found, {"layers": ["base"], "next": "^/light", "light": "^/light",
                                 "mode": "light", "saves": False, "must_not": ["c"]})

    def test_light_run_without_its_own_checks(self):
        found = run.light({"layers": ["base"], "next": "^/full", "must_not": ["b"], "light": "^/light"})
        self.assertEqual(found["must_not"], [])
        self.assertNotIn("must", found)

    def test_light_must_not_fails_a_light_answer(self):
        light = run.light({"layers": ["base"], "light": "^/to-tickets", "light_must_not": [TICKET_GATE]})
        answer = ("Done up to step 9: stories refined.\n**Step 10, Tickets** · architect · "
                  "gate: you approve the tickets before they are published\n\n**Next**\n```\n/to-tickets 1\n```\n")
        self.assertEqual(len(run.grade(light, answer)), 1)
        self.assertEqual(run.grade(light, answer.replace("gate: you approve the tickets before they are published",
                                                          "no gate: you confirm the breakdown in that session")), [])


class Report(unittest.TestCase):
    """The report names a check, quotes the sentence that fails it, and keeps its tables whole."""
    OUTCOME = {"name": "x", "number": 1, "answer": "**Next**\n```\n/a | b\n```\n", "failures": None}

    def write(self, scenario, gate="you approve the tickets"):
        answer = f"**Gate:** {gate}.\n" + self.OUTCOME["answer"]
        outcome = dict(self.OUTCOME, failures=run.grade(scenario, answer), models=["model"], cost=0)
        tested = {"tree": "tree", "blob": "blob", "sha": "0" * 40, "dirty": False}
        with unittest.mock.patch.object(run, "claude_version", return_value="1"), \
                unittest.mock.patch.object(run, "pinned", return_value={}):
            return run.report({"x": scenario}, {"x": [outcome]}, tested, None)

    def test_a_check_shows_its_name_and_the_sentence(self):
        scenario = {"layers": ["base"], "why": "why", "mode": "light", "next": "^/a", "must_not": [TICKET_GATE]}
        self.assertEqual(run.grade(scenario, "**Gate:** you approve the tickets.\n" + self.OUTCOME["answer"]),
                         ["answer fails the check 'old ticket gate': \"you approve the tickets\""])
        report = self.write(scenario, gate="you approve the tickets | then they publish")
        self.assertIn("the answer passes the check 'old ticket gate' in checks.py", report)
        row = next(line for line in report.splitlines() if line.startswith("| 1 |"))
        self.assertEqual(len(re.findall(r"(?<!\\)\|", row)), 4, row)

    def test_a_pattern_shows_whole(self):
        self.assertEqual(run.grade({"mode": "light", "must_not": ["approve"]}, "approve\n" + self.OUTCOME["answer"]),
                         ["answer has /approve/"])

    def test_verdict_cells_keep_the_table(self):
        report = self.write({"layers": ["base"], "why": "why", "mode": "light", "next": "^/c", "must_not": ["a|b"]})
        row = next(line for line in report.splitlines() if line.startswith("| 1 |"))
        self.assertEqual(len(re.findall(r"(?<!\\)\|", row)), 4, row)


if __name__ == "__main__":
    unittest.main()
