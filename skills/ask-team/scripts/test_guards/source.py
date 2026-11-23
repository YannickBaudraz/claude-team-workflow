"""A test file read for the guards: its lines with comments and strings emptied, the brackets open
on each line, its groups of tests, and the tests it defines."""
import os
import re

from .languages import LANGUAGES, LEXERS, language_of

# How far a marker or a skip decorator may sit above the declaration it applies to.
REACH = 6


def lex(path, text):
    """A file's lines twice over, with comments emptied: once with its strings as written, to
    read test names, and once with their text emptied, to read skips and markers. A string that
    spans lines is emptied in both. Line numbers stay as in the file."""
    extension = os.path.splitext(path)[1].lower()
    lexer = LEXERS.get(extension) or LEXERS[language_of(path)]
    named, bare, at = [], [], 0
    blank = lambda span: re.sub(r"[^\n]", " ", span)
    for match in lexer.finditer(text):
        span = match.group()
        named.append(text[at:match.start()])
        bare.append(text[at:match.start()])
        if match.lastgroup.startswith("comment") or "\n" in span:
            named.append(blank(span))
            bare.append(blank(span))
        else:
            named.append(span)
            bare.append(span[0] + blank(span[1:-1]) + span[-1] if len(span) > 1 else span)
        at = match.end()
    named.append(text[at:])
    bare.append(text[at:])
    return "".join(named).split("\n"), "".join(bare).split("\n")


def first_group(match):
    return next((group for group in match.groups() if group is not None), "").strip("`").strip()


def named(language, text, kinds=("named",)):
    for kind in kinds:
        for pattern in language[kind]:
            match = pattern.search(text)
            if match:
                return first_group(match)
    return None


class Source:
    """A test file's lines as written (raw), with comments emptied (code), and with strings
    emptied as well (bare)."""

    def __init__(self, path, text):
        self.language = LANGUAGES[language_of(path)]
        self.raw = text.split("\n")
        self.code, self.bare = lex(path, text)
        # The brackets still open where each line starts, as (line index, column), outermost
        # first; one more entry holds those open at the end of the file.
        self.open, stack = [], []
        for index, text in enumerate(self.bare):
            self.open.append(tuple(stack))
            stack = opened(stack, index, text)
        self.open.append(tuple(stack))
        # The groups of tests, as (name, first line index, last line index, whether its tests run).
        self.groups = []
        for index, text in enumerate(self.code):
            name = named(self.language, text, ("group",))
            if name:
                self.groups.append((name, index, extent(self.code, index), runs(self.language, text, name)))

    def chain(self, index, own=True):
        """The names of the groups around line `index`, outermost first, with the name on the line
        itself when own; joined by ::, as pytest names a test in a class."""
        names = [name for name, first, last, _ in self.groups if first < index <= last]
        name = named(self.language, self.code[index], ("named", "group", "declaration", "function")) if own else None
        return "::".join(names + ([name] if name else []))

    def collected(self, index):
        """Whether the runner collects a test on line `index`: not in a class pytest leaves out."""
        return all(ran for _, first, last, ran in self.groups if first < index <= last)

    def closing(self, index):
        """The index of the line where the brackets that line `index` opens are closed again."""
        depth = len(self.open[index])
        return next((at for at in range(index, len(self.bare)) if len(self.open[at + 1]) <= depth),
                    len(self.bare) - 1)

    def innermost(self, index, column):
        """The line index and column of the innermost bracket open at a column of a line, or None."""
        stack = opened(list(self.open[index]), index, self.bare[index][:column])
        return stack[-1] if stack else None

    def is_comment(self, number):
        """Whether line `number` (1-based) holds a comment and nothing else."""
        return bool(self.raw[number - 1].strip()) and not self.code[number - 1].strip()

    def is_marker(self, number):
        if any(pattern.search(self.bare[number - 1]) for pattern in self.language["marker"]):
            return True
        return self.is_comment(number) and any(pattern.search(self.raw[number - 1])
                                                for pattern in self.language["doc_marker"])


def opened(stack, index, text):
    """stack, the brackets open before a line's text, as (line index, column), with the text's
    own brackets opened and closed; a closing bracket with none open is ignored."""
    stack = list(stack)
    for column, character in enumerate(text):
        if character in "([{":
            stack.append((index, column))
        elif character in ")]}" and stack:
            stack.pop()
    return stack


def runs(language, text, name):
    """Whether a group's tests run: pytest collects a class only when its name starts with Test,
    unless it has a base, as a unittest TestCase."""
    if language is not LANGUAGES["python"] or name.startswith("Test"):
        return True
    return bool(re.search(r"\(\s*(?!object\s*\))[^)\s]", text))


def extent(lines, index):
    """The index of the last line of the block that starts at lines[index]: the lines indented
    under its first line, and the one closing it."""
    depth, last = indent(lines[index]), index
    for at in range(index + 1, len(lines)):
        stripped = lines[at].strip()
        if not stripped:
            continue
        if indent(lines[at]) > depth:
            last = at
            continue
        if indent(lines[at]) == depth and (stripped[0] in ")]}" or re.match(r"end\b", stripped)):
            last = at
        break
    return last


def body(lines, index):
    """The stripped lines of the test that starts at lines[index]."""
    return tuple(text.strip() for text in lines[index:extent(lines, index) + 1] if text.strip())


def definitions(source):
    """The tests a file defines, in order, as (name, body, line number). A marker applies to the
    next declaration, when it sits at most REACH lines above it."""
    language, found, marked = source.language, [], None
    for index, text in enumerate(source.code):
        number = index + 1
        if source.is_marker(number):
            name = named(language, text, ("declaration",))
            if name:
                found.append((name, body(source.code, index), number))
                marked = None
            else:
                marked = number
            continue
        name = named(language, text)
        if name:
            found.append((name, body(source.code, index), number))
            marked = None
            continue
        name = named(language, text, ("declaration",)) if marked is not None else None
        if name:
            if number - marked <= REACH:
                found.append((name, body(source.code, index), number))
            marked = None
    return [test for test in found if source.collected(test[2] - 1)]


def is_attachment(text):
    """A line that may sit between a skip decorator and what it skips: a decorator, an
    annotation or attribute, a blank line, or one that held only a comment."""
    stripped = text.strip()
    return not stripped or stripped[0] in "@#["


def indent(text):
    return len(text) - len(text.lstrip())
