"""Unit tests for skills/ask-team/scripts/flow.py, on invented tables only.

Run: python3 -m unittest discover tests/flow
"""
import os
import sys
import unittest

# The page imports flow.py too, and must never run a stale cached copy of it (see build-workflow.py).
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "ask-team", "scripts"))

import flow

FLOW = """# The flow

## Main flow

| # | Step | Command | Output, and the gate before moving on |
|---|---|---|---|
| 1 | Discovery | `/grill` | Shared understanding. |
| 2 | Fog (only when the way is unclear) | `/map` | Decisions. |
| 3 | PRD, per epic | `/prd <epic>` | The PRD. Approved. |
| 4 | Approval | `gh pr merge` | The user merges. |

Prose after the table, with a | pipe.

## Step contracts

| Step | Needs | Makes |
|---|---|---|
| 1 | idea (outside) | terms, ADRs |
| 2 | — | decisions |
| 3 | terms or decisions, design (when the epic has a screen) | PRD |
| `/change` | change (outside) or issue, terms | issue |

| Output | Made by | Lives in |
|---|---|---|
| terms | `/grill`, `domain` | Glossary |
| PRD | the user | `docs/prd.md` |

## Sessions

Not a table.
"""

REGISTRY = """# Registry

## Workflow skills

| Command | Source | Visibility | Used at | Calls | Does |
|---|---|---|---|---|---|
| `/ask` | `me/repo` | typed | entry point, any time |  | Routes. |
| `/build` | `me/repo` | typed | 11 Build, pairing, or alone | a, b | Builds. |

## Step triggers and measures

| Step | Trigger | Paid by | Upkeep |
|---|---|---|---|
| Plain text | a fact | a step | none |

## Denied duplicates

| Command | Source | Visibility | Duplicates |
|---|---|---|---|
| `other:thing` | `them/repo` | denied | `/build` |
"""


class Section(unittest.TestCase):
    def test_a_section_runs_to_the_next_section(self):
        self.assertEqual(flow.section("## A\none\n\n## B\ntwo\n", "A"), "one\n\n")

    def test_the_last_section_runs_to_the_end(self):
        self.assertEqual(flow.section("## A\none\n\n## B\ntwo\n", "B"), "two\n")

    def test_a_deeper_heading_stays_inside_it(self):
        self.assertEqual(flow.section("## A\none\n### B\ntwo\n", "A"), "one\n### B\ntwo\n")

    def test_a_section_may_be_empty(self):
        self.assertEqual(flow.section("## A\n## B\n", "A"), "")

    def test_no_such_section_is_none_not_empty(self):
        self.assertIsNone(flow.section("## A\none\n", "B"))

    def test_a_title_is_matched_literally(self):
        self.assertIsNone(flow.section("## Main flow\none\n", "Main.flow"))


class Tables(unittest.TestCase):
    def test_a_table_is_its_rows_of_cells_without_the_separator(self):
        self.assertEqual(flow.tables("| a | b |\n|---|:-:|\n| 1 | 2 |\n"), [[["a", "b"], ["1", "2"]]])

    def test_any_other_line_ends_a_table(self):
        self.assertEqual(len(flow.tables("| a |\n|---|\n| 1 |\n\n| b |\n|---|\n| 2 |\n")), 2)

    def test_empty_cells_are_kept(self):
        self.assertEqual(flow.tables("| a | b | c |\n| 1 |  | 3 |\n")[0][1], ["1", "", "3"])

    def test_indentation_and_trailing_spaces_do_not_matter(self):
        self.assertEqual(flow.tables("  | a |  \n  | 1 |  \n"), [[["a"], ["1"]]])

    def test_no_table_is_no_tables(self):
        self.assertEqual(flow.tables("just prose\n"), [])


class Records(unittest.TestCase):
    def test_rows_are_keyed_by_the_header_in_lower_case(self):
        self.assertEqual(flow.records([["Used At", "Does"], ["1", "x"]]), [{"used at": "1", "does": "x"}])

    def test_a_short_row_lacks_the_last_keys(self):
        self.assertEqual(flow.records([["A", "B"], ["1"]]), [{"a": "1"}])

    def test_a_table_with_only_its_header_has_no_records(self):
        self.assertEqual(flow.records([["A", "B"]]), [])


class MainFlow(unittest.TestCase):
    def test_rows_keep_their_number_and_the_cells_after_it(self):
        self.assertEqual(flow.main_flow(FLOW)[0], (1, ["Discovery", "`/grill`", "Shared understanding."]))

    def test_only_numbered_rows_of_that_section_count(self):
        self.assertEqual([number for number, _ in flow.main_flow(FLOW)], [1, 2, 3, 4])

    def test_a_row_with_the_wrong_columns_is_kept_as_it_stands(self):
        text = "## Main flow\n| 1 | a | b | c | d |\n| 2 | a |\n"
        self.assertEqual(flow.main_flow(text), [(1, ["a", "b", "c", "d"]), (2, ["a"])])

    def test_no_section_is_no_rows(self):
        self.assertEqual(flow.main_flow("## Other\n| 1 | a | b | c |\n"), [])


class Steps(unittest.TestCase):
    def setUp(self):
        self.steps = flow.steps(FLOW)

    def test_they_are_keyed_by_number_in_file_order(self):
        self.assertEqual(list(self.steps), [1, 2, 3, 4])

    def test_a_plain_step(self):
        self.assertEqual(self.steps[1], dict(number=1, name="Discovery", qual="", note="", optional=False,
                                             command="`/grill`", output="Shared understanding.", gate=False))

    def test_a_note_in_brackets_and_an_optional_step(self):
        step = self.steps[2]
        self.assertEqual((step["name"], step["note"], step["optional"]), ("Fog", "only when the way is unclear", True))

    def test_the_part_after_the_comma_qualifies_the_step(self):
        self.assertEqual((self.steps[3]["name"], self.steps[3]["qual"]), ("PRD", "per epic"))

    def test_a_note_about_something_else_leaves_a_step_required(self):
        steps = flow.steps("## Main flow\n| 1 | Review (fresh session) | `/review` | Verdict. |\n")
        self.assertEqual((steps[1]["note"], steps[1]["optional"]), ("fresh session", False))

    def test_an_approved_output_is_a_gate_and_so_is_a_merge(self):
        self.assertEqual([number for number, step in self.steps.items() if step["gate"]], [3, 4])

    def test_a_row_without_four_columns_is_an_error_naming_it(self):
        with self.assertRaisesRegex(flow.SourceError, "Main flow row 1 should have four columns"):
            flow.steps("## Main flow\n| 1 | a | b |\n")


class Approved(unittest.TestCase):
    def test_the_word_counts_in_any_case(self):
        self.assertTrue(flow.approved("Both APPROVED by the user."))

    def test_the_merge_is_not_an_approval(self):
        self.assertFalse(flow.approved("The user merges."))

    def test_only_the_whole_word_counts(self):
        self.assertFalse(flow.approved("Unapproved drafts."))


class StepContracts(unittest.TestCase):
    def setUp(self):
        self.contracts, self.outputs = flow.step_contracts(FLOW)

    def test_steps_are_keyed_by_number_and_ways_in_by_their_command(self):
        self.assertEqual([key for key, _, _ in self.contracts], [1, 2, 3, "/change"])

    def test_what_a_step_makes_is_a_list(self):
        self.assertEqual(self.contracts[0][2], ["terms", "ADRs"])

    def test_a_dash_needs_nothing(self):
        self.assertEqual(self.contracts[1][1], [])

    def test_an_or_groups_alternatives_and_a_when_is_dropped(self):
        self.assertEqual(self.contracts[2][1], [["terms", "decisions"], ["design"]])

    def test_outside_stays_for_the_contract_check_to_read(self):
        self.assertEqual(self.contracts[3][1], [["change (outside)", "issue"], ["terms"]])

    def test_an_output_has_its_makers_without_backticks_and_its_home(self):
        self.assertEqual(self.outputs[0], ("terms", ["/grill", "domain"], "Glossary"))

    def test_a_backticked_home_stays_as_written(self):
        self.assertEqual(self.outputs[1], ("PRD", ["the user"], "`docs/prd.md`"))

    def test_the_section_must_hold_two_tables(self):
        self.assertIsNone(flow.step_contracts("## Step contracts\n| a |\n| 1 |\n"))

    def test_no_section_has_no_contracts(self):
        self.assertIsNone(flow.step_contracts("## Other\n"))


class WorkflowTables(unittest.TestCase):
    def test_only_the_table_with_a_does_column_counts(self):
        found = flow.workflow_tables(REGISTRY)
        self.assertEqual([[row["command"] for row in table] for table in found], [["`/ask`", "`/build`"]])

    def test_a_short_first_row_does_not_hide_the_column(self):
        self.assertEqual(flow.workflow_tables("| Command | Does |\n|---|---|\n| `/a` |\n"), [[{"command": "`/a`"}]])

    def test_a_table_with_no_rows_does_not_count(self):
        self.assertEqual(flow.workflow_tables("| Command | Does |\n|---|---|\n"), [])


class SkillRows(unittest.TestCase):
    def setUp(self):
        self.rows = list(flow.skill_rows(REGISTRY))

    def test_a_skill_of_any_table_counts_and_a_plain_first_cell_does_not(self):
        self.assertEqual([row["command"] for row in self.rows], ["/ask", "/build", "other:thing"])

    def test_it_keeps_the_columns_the_registry_check_reads(self):
        self.assertEqual(self.rows[1], {"command": "/build", "source": "`me/repo`", "visibility": "typed",
                                        "calls": "a, b", "does": "Builds."})

    def test_a_table_without_calls_or_does_says_so(self):
        self.assertEqual((self.rows[2]["calls"], self.rows[2]["does"]), ("", None))


class UsedAt(unittest.TestCase):
    def test_a_step_alone(self):
        self.assertEqual(flow.used_at({"used at": "6 PRD"}), (6, ""))

    def test_what_follows_the_first_comma_comes_with_it(self):
        self.assertEqual(flow.used_at({"used at": "11 Build, pairing, or alone"}), (11, "pairing, or alone"))

    def test_words_name_no_step(self):
        self.assertEqual(flow.used_at({"used at": "way in, then any time"}), (None, ""))

    def test_a_number_inside_a_word_is_no_step(self):
        self.assertEqual(flow.used_at({"used at": "2nd pass"}), (None, ""))

    def test_a_row_without_the_column_names_no_step(self):
        self.assertEqual(flow.used_at({}), (None, ""))


if __name__ == "__main__":
    unittest.main()
