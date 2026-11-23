"""The reasons a pull request's description gives for each listed change, read as the page shows it."""
import html
import re

PLACEHOLDER = "<one-line reason>"
KINDS = {"deleted": r"deleted", "newly skipped": r"(?:newly\s+)?skipped", "changed": r"changed"}
KIND_WORDS = {"deleted", "removed", "newly", "skipped", "edited", "moved", "renamed", "changed"}


def readable(body):
    """The description as the page shows it: without HTML comments, fenced code blocks or link
    reference definitions, whose title text never shows."""
    body = re.sub(r"<!--.*?(?:-->|\Z)", "", body, flags=re.S)
    shown, fence = [], None
    for line in body.splitlines():
        opening = re.match(r"\s*(`{3,}|~{3,})", line)
        if fence is None and opening:
            fence = opening.group(1)
        elif fence is not None and line.strip().startswith(fence[0] * len(fence)) and not line.strip().strip(fence[0]):
            fence = None
        elif fence is None and not re.match(r"\s{0,3}\[[^\]]+\]:\s", line):
            shown.append(line)
    return shown


def reason(body, key, kind):
    """The reason the description gives for key, or None. The line must have the printed shape:
    the key whole, its kind, maybe its line, then a colon, a dash or a table bar, and a reason that
    is neither the placeholder nor a kind word. A key stands whole: `adds` is not read in
    `adds two`, nor `test_remove` in `test_remove_all`."""
    shape = re.compile(r"(?<![\w./-])" + re.escape(key) + r"`?\s+" + KINDS[kind]
                       + r"\b(?:\s*\((?:old |new )?line \d+\))?\s*[:|\-–—]+(.*)$")
    for line in readable(body):
        match = shape.search(line)
        if not match:
            continue
        rest = match.group(1).strip().strip("|").strip()
        words = re.findall(r"[^\W_]+", rest.lower())
        # The placeholder left in place, even in code, emphasis or an HTML entity, or followed by
        # punctuation, is no reason; a reason that starts like it, as `<Button> was removed`, is.
        bare = re.sub(r"[`*_~]", "", html.unescape(rest)).strip().rstrip(".,;:!?").strip()
        if bare == PLACEHOLDER or not words or set(words) <= KIND_WORDS:
            continue
        return rest
    return None
