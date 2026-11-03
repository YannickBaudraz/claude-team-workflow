"""The one reader of the workflow's tables: FLOW.md's Main flow and Step contracts, and REGISTRY.md.

check-contracts.py, check-registry.py and the workflow page (docs/workflow/sources.py) read these
files through here, so a change to their structure changes one parser. Every function takes a
file's text and returns what its tables say; what a caller does about a wrong value stays with it.
"""
import re


class SourceError(Exception):
    """A source no longer has the shape the page is built from."""


def need(ok, message):
    if not ok:
        raise SourceError(message)


def section(text, title):
    """What the `## title` section holds, or None when text has no such section."""
    match = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1) if match else None


def tables(text):
    """Every markdown table in text, as a list of rows of cells, header first."""
    found, current = [], None
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            current = None
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        if current is None:
            current = []
            found.append(current)
        current.append(cells)
    return found


def records(table):
    """A table's rows as dicts, keyed by its column headers in lower case."""
    header = [cell.lower() for cell in table[0]]
    return [dict(zip(header, cells)) for cells in table[1:]]


def main_flow(text):
    """Main flow's rows in file order, as (step number, the cells after it), whatever their count.
    steps() is the same table with each row read in full."""
    found = []
    for line in (section(text, "Main flow") or "").splitlines():
        row = re.match(r"\|\s*(\d+)\s*\|(.*)\|\s*$", line)
        if row:
            found.append((int(row.group(1)), [cell.strip() for cell in row.group(2).split("|")]))
    return found


def approved(output):
    """Whether a Main flow output has to be approved."""
    return bool(re.search(r"\bapproved\b", output, re.I))


def steps(text):
    """Main flow's steps by number. "Fog, per epic (only when ...)" gives the name Fog, the qualifier
    per epic and the note. Raises SourceError on a row without its four columns."""
    found = {}
    for number, cells in main_flow(text):
        need(len(cells) == 3, f"Main flow row {number} should have four columns")
        step, command, output = cells
        note = ""
        if "(" in step:
            step, note = step.split("(", 1)
            note = note.rstrip(")").strip()
        name, _, qual = (part.strip() for part in step.partition(","))
        found[number] = dict(
            number=number, name=name, qual=qual, note=note,
            optional=note.lower().startswith("only"), command=command, output=output,
            # A gate is a step whose output has to be approved, or that you merge.
            gate=approved(output) or bool(re.search(r"\bmerges\b", output, re.I)))
    return found


def step_contracts(text):
    """Step contracts' two tables as (steps, outputs), or None when the section does not hold two.

    A step is (key, needs, makes): its number, or the command of a way in; the groups it needs, where
    "a or b, c" is [[a, b], [c]]; the outputs it leaves. An output is (name, makers, home)."""
    found = tables(section(text, "Step contracts") or "")
    if len(found) != 2:
        return None
    contracts = []
    for key, needs, makes in found[0][1:]:
        contracts.append((
            int(key) if key.isdigit() else key.strip("`"),
            # "interface design (when the epic has a graphical interface)": needed only in that case, made earlier all the same.
            [[re.sub(r"\s*\(when [^)]*\)$", "", alt.strip()) for alt in group.split(" or ")]
             for group in needs.split(",") if group.strip() not in ("", "—")],
            [output for output in (name.strip() for name in makes.split(",")) if output]))
    outputs = [(output, [maker.strip().strip("`") for maker in makers.split(",")], home)
               for output, makers, home in found[1][1:]]
    return contracts, outputs


def workflow_tables(text):
    """REGISTRY.md's tables with a Does column and at least one row, as records. There is one."""
    return [records(table) for table in tables(text)
            if table[1:] and "does" in (cell.lower() for cell in table[0])]


def skill_rows(text):
    """Every row of REGISTRY.md that names a skill, in whichever table: its first cell is backticked."""
    for table in tables(text):
        for cells, row in zip(table[1:], records(table)):
            if cells[0].startswith("`"):
                yield {"command": cells[0].strip("`"), "source": row["source"],
                       "visibility": row["visibility"], "calls": row.get("calls", ""),
                       "does": row.get("does")}


def used_at(row):
    """A registry row's Used at, as (step, what follows the first comma): "11 Build, pairing" gives
    (11, "pairing"). The step is None when the column names none, as "way in" does."""
    match = re.match(r"(\d+)\b[^,]*(?:,\s*(.*))?$", row.get("used at", ""))
    return (int(match.group(1)), match.group(2) or "") if match else (None, "")
