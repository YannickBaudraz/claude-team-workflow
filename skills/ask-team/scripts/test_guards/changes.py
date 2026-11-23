"""What a pull request does to the tests: the tests it deletes, the tests it newly skips, and the
changes to the files a guard names."""
import re
from collections import Counter

from .languages import by_name, is_test_file
from .source import REACH, Source, definitions, extent, indent, is_attachment, named

def skipped_line(source, number):
    """The index of the line that names what the skip on line `number` (1-based) of a file skips:
    the test or group on its line, below it when the skip is a decorator or an annotation, or
    around it when it sits in its body. A skip inside the brackets of a decorator that spans
    lines, as a wrapped skipif or one case's marks in a parametrize, is read from that decorator's
    line. A skip in a helper or a fixture names that function, so it covers no test, unless the
    function sits inside a test. None for the whole file."""
    language, lines = source.language, source.code
    outer = source.open[number - 1]
    if outer and is_attachment(lines[outer[0][0]]):
        number = outer[0][0] + 1
    kinds = ("named", "group", "declaration", "function")
    text = lines[number - 1]
    if named(language, text, kinds):
        return number - 1
    if not text.strip():
        return None
    if is_attachment(text):
        # Below the line that closes the decorator's brackets, when it leaves them open.
        end = source.closing(number - 1) + 1
        for at in range(end, min(end + REACH, len(lines))):
            if named(language, lines[at], kinds):
                return at
            if not is_attachment(lines[at]):
                break
    # A skip on a closing line, as Dart's `}, skip: true);`, belongs to the block it closes.
    depth = indent(text) + (text.strip()[0] in ")]}")
    function = None
    for at in range(number - 2, -1, -1):
        above = lines[at]
        if above.strip() in ("", "{") or indent(above) >= depth:
            continue
        if named(language, above, ("named", "declaration")):
            return at
        if named(language, above, ("group",)):
            return at if function is None else function
        if function is None and named(language, above, ("function",)):
            function = at
        depth = indent(above)
    return function


def skips(source):
    """The skips a file holds, as (the skip's line, what it skips or None for the whole file, line
    number, the first and last line index of what it skips, the name a skip mark is saved under
    on that line or None). What it skips is named with the groups around it, as
    TestCart::test_empty, so the same skip on a test of the same name in another group is another
    skip. A line that saves a skip mark under a name, as `requires_db = mark.skipif(...)`, is a
    skip named after that name that covers only its own line, so a changed definition is listed;
    each `@requires_db` is a skip of its test, and a pytestmark that names it, of the file."""
    language, found = source.language, []
    aliases = {match.group(1) for text in source.bare for pattern in language["alias"]
               for match in [pattern.search(text)] if match}
    names = "|".join(map(re.escape, sorted(aliases)))
    alias = re.compile(r"^\s*@(?:%s)\b" % names) if aliases else None
    mentioned = re.compile(r"(?<![\w.])(?:%s)\b" % names) if aliases else None
    pytestmark = re.compile(r"^\s*pytestmark\s*=")
    for index, text in enumerate(source.bare):
        line = source.code[index].strip() or source.raw[index].strip()
        saved = next((match.group(1) for pattern in language["alias"] for match in [pattern.search(text)] if match),
                     None)
        if saved:
            what = "::".join(filter(None, (source.chain(index, own=False), saved)))
            found.append((line, what, index + 1, index, index, saved))
            continue
        outer = source.open[index]
        if any(pattern.search(source.raw[index]) for pattern in language["raw_skips"]):
            target = None
        elif any(pattern.search(text) for pattern in language["file_skips"]):
            target = None
        elif mentioned and mentioned.search(text) and (
                pytestmark.match(text) or (outer and pytestmark.match(source.bare[outer[0][0]]))):
            target = None
        elif (any(pattern.search(text) for pattern in language["skips"]) or in_attribute(source, index)
              or (alias and alias.search(text))):
            target = skipped_line(source, index + 1)
        else:
            continue
        if target is None:
            found.append((line, None, index + 1, 0, len(source.code) - 1, None))
        else:
            found.append((line, source.chain(target), index + 1, target, extent(source.code, target), None))
    return found


def under(source, found):
    """Each test of a file, named with its groups, with the skips that apply to it: its own, its
    groups' and its file's, as a set of (the skip's line, what it skips)."""
    return [("::".join(filter(None, (source.chain(number - 1, own=False), name))), number,
             {(line, what) for line, what, _, first, last, _ in found if first <= number - 1 <= last})
            for name, _, number in definitions(source)]


def in_attribute(source, index):
    """Whether line `index` holds a skip that counts only inside an attribute's brackets, with that
    attribute opened on an earlier line, as a Swift Testing trait list that wraps."""
    for skip, attribute in source.language["traits"]:
        for match in skip.finditer(source.bare[index]):
            opener = source.innermost(index, match.start())
            if opener and opener[0] < index and attribute.search(source.bare[opener[0]][:opener[1] + 1]):
                return True
    return False


def unpaired(tests, pool, key):
    """The tests that find no match in pool, a Counter of keys; each match uses one up."""
    left = []
    for test in tests:
        if pool[key(test)]:
            pool[key(test)] -= 1
        else:
            left.append(test)
    return left


def first_lines(found):
    """found, (key, line) pairs, with each key once, at its first line."""
    first = {}
    for key, number in found:
        first.setdefault(key, number)
    return list(first.items())


def leaves(old, new, extra=()):
    """Whether a test file is deleted, or renamed to a path its runner no longer collects: one
    that is no test file, or one that is a test file only by its folder when its name made it
    one before, as tests/test_cart.py renamed tests/cart_checks.py."""
    return is_test_file(old, extra) and (not is_test_file(new, extra) or (by_name(old, extra)
                                                                           and not by_name(new, extra)))


def deleted_tests(files, read_old, read_new, extra=()):
    """Every deleted test as (path::name, its line in the old file), or (path, None) for a test
    file taken away whole. read_old and read_new give a file's text on each side of the diff. A
    test from a file named as a test file has moved only to another file named as one."""
    name = lambda test: test[0]
    sides, spare = [], Counter()
    for entry in files:
        old, new = entry["old"], entry["new"]
        before = definitions(Source(old, read_old(old))) if is_test_file(old, extra) else []
        kept = is_test_file(new, extra) and not leaves(old, new, extra)
        after = definitions(Source(new, read_new(new))) if kept else []
        sides.append((entry, before, unpaired(before, Counter(map(name, after)), name)))
        added = unpaired(after, Counter(map(name, before)), name)
        spare.update((test, text, by_name(new, extra)) for test, text, _ in added)
    found = []
    for entry, before, gone in sides:
        old = entry["old"]
        named_file = by_name(old, extra)
        left = []
        for test, text, number in gone:
            for key in ((test, text, True),) + (() if named_file else ((test, text, False),)):
                if spare[key]:
                    spare[key] -= 1
                    break
            else:
                left.append((test, text, number))
        if leaves(old, entry["new"], extra):
            if left or (not before and named_file):
                found.append((old, None))
            continue
        found.extend((f"{old}::{test}", number) for test, _, number in left)
    return first_lines(found)


def skipped_tests(files, read_old, read_new, extra=()):
    """Every newly skipped test, as (path::name, the skip's line in the new file), or the path in
    place of path::name when the whole file is skipped. A skip the old file held on the same test,
    in the same groups, with the same line, is not new. A test that a skip the old file held now
    applies to, and did not before, is listed too, at its own line: one moved into a skipped
    group or class, or into a file skipped whole, or added there."""
    found = []
    for entry in files:
        old, new = entry["old"], entry["new"]
        if not is_test_file(new, extra):
            continue
        # The old file is read in the new one's language, even when it was no test file then.
        before = Source(new, read_old(old) if old else "")
        after = Source(new, read_new(new))
        old_skips, new_skips = skips(before), skips(after)
        held = Counter((text, what) for text, what, *_ in old_skips)
        # A skip mark saved under a new name skips nothing until a test or a pytestmark uses it.
        saved_before = {saved for *_, saved in old_skips if saved}
        for text, what, number, _, _, saved in new_skips:
            if held[(text, what)]:
                held[(text, what)] -= 1
            elif not saved or saved in saved_before:
                found.append((f"{new}::{what}" if what else new, number))
        kept = {(text, what) for text, what, *_ in old_skips}
        had = {}
        for test, _, applied in under(before, old_skips):
            had.setdefault(test, set()).update(applied)
        for test, number, applied in under(after, new_skips):
            if any(skip in kept and skip not in had.get(test, ()) for skip in applied):
                found.append((f"{new}::{test}", number))
    return first_lines(found)


def changed_guards(files, guards):
    """Each file the diff changes that a guard names, as (path, None): the guard's own file, or a
    file in the guard's folder, written with or without a closing /."""
    found = []
    for entry in files:
        for path in filter(None, (entry["new"], entry["old"])):
            if any(path == guard.rstrip("/") or path.startswith(guard.rstrip("/") + "/") for guard in guards):
                found.append((path, None))
                break
    return first_lines(found)
