"""Checks on the router's answer that a regex would read badly. A scenario names one in must_not or
light_must_not as {"check": "<name>"}; the check returns the text that fails it, or None.

A check reads the router's wording for the forms it writes in normal work, by habit or by mistake. It
does not stop wording made to slip past it: the person who reads a paid run's answers catches that.
"""
import re

# A sentence, or a part set off by a colon or the light answer's dots: in "Step 10 runs in the same session:
# `/to-tickets 1`, and you approve the tickets", the session and the approval are apart.
SENTENCE = re.compile(r"[.:;!?·\n]")
# Brackets set off a piece of a sentence: in "`/to-tickets 1` (gate: you approve the tickets), then `/build-ticket`
# and its review", the review is not the approval's. A session in brackets still sets the whole sentence in it.
PIECE = re.compile(r"[()\[\]]")
# Words that start a clause of their own: in "nothing is built until you approve the tickets", the
# negation and the approval sit in two clauses.
CLAUSE = re.compile(r",|\s[—–-]\s|(?=\b(?:until|till|unless|before|once|after|when|whenever|while|but|then|and"
                    r"|or|so|if|without|except|besides|beyond|instead\s+of|rather\s+than|other\s+than|apart\s+from"
                    r"|aside\s+from)\b)", re.I)
NEGATION = re.compile(r"\b(?:no|not|never|nothing|none|nobody\w*|neither|nor|cannot|instead|rather|\w+n['’]t)\b"
                      r"|\bwithout\b(?!\s+(?:your|you)\b)", re.I)
# What a piece of a sentence names: the breakdown (whose approval is the confirmation itself), the tickets
# (step 10 and its command included), another step, command or thing the flow approves, a pronoun, or an approval.
THING = re.compile(r"(?P<breakdown>\btickets?['’]?s?\s+(?:breakdown|split|slices?|plan|list)\b"
                   r"|\b(?:breakdown|split|slices|slicing|plan)\b)"
                   r"|(?P<tickets>\bsteps?\s+\d+['’]?s?\s+tickets?\b|(?<![\w/-])tickets?\b|\bstep\s+10\b"
                   r"|(?<![\w.])/to-tickets\b)"
                   r"|(?P<other>\bsteps?\s+\d+\b|(?<![\w.])/[a-z][\w-]*|\b(?:PRDs?|designs?|docs?|stor(?:y|ies)|epics?"
                   r"|spec\w*|roadmap|brief)\b)"
                   r"|(?P<pronoun>\b(?:them|it)\b)"
                   r"|(?P<approval>\bapprov\w*|\baccept(?:s|ed|ing)?\b|\bsign(?:s|ed|ing)?[\s-]?off\b|\bokay\w*"
                   r"|(?-i:\bOK(?:ed|'d)?\b)|\bgo-ahead\b|\bgated\b)", re.I)
# A thing named right after the tickets to qualify them, "tickets for stories #3 and #4", "the tickets of each
# story", leaves the tickets as the last thing named.
QUALIFIER = re.compile(r"\b(?:for|of|from|per|under)\s+(?:\S+\s+){0,2}$", re.I)
# An approval asked for with a verb ("you approve", "or change the PRD") is about what follows it; one stated
# as a noun or a participle ("your approval", "approved before publishing") is about what came before.
STATED = re.compile(r"approv(?:al|ed)|accepted|okayed|OK(?:ed|'d)|signed|go-ahead|gated", re.I)
# "The approved stories", "an approving review": an approval another step gave, not one waited on.
ADJECTIVE = re.compile(r"\b(?:the|a|an|its|their|each|every|your)\s+$", re.I)
# A sentence that sets its approval in the session ("in this session you approve the tickets", "you approve
# them in the `/to-tickets` session", "(in the same session)", "part of the session", "in-session") is the
# confirmation, in whatever order it puts its words. A session named as a role, "(architect session, approved
# by publishing)", or another step's, "then `/build-ticket` in a developer session", is not. A piece of a
# sentence that names the review, the acceptance verdict, a PR or the merge speaks of steps 12 and 13, though
# "you review and approve" is yours.
CONFIRMATION = re.compile(r"\b(?:in|during|within|of)\s+(?!(?:a|an|another)\s)(?:[\w'’`/-]+\s+){0,4}?session\b"
                          r"|\bsame\s+session\b|\bin-session\b", re.I)
# A sentence that opens on one of these sets its first clause before its subject: in "once you approve it, the
# ticket is published", "it" stands for the ticket named after it.
LEADING = re.compile(r"^\W*(?:once|when|whenever|after|until|till|as\s+soon\s+as|if|before)\b", re.I)
LATER_STEP = re.compile(r"(?<!you\s)\breview|\bacceptance\b|\bverdict|\bmerg|\bPRs?\b|\bpull\s+request", re.I)


def gate_parts(answer):
    """Where an answer can state step 10's gate: the Gate line, a line that opens on step 10 (the light answer's
    carries its gate), and After that, up to the next bold label or code block, later steps included."""
    parts, after = [], None
    for line in answer.splitlines():
        if after is not None and re.match(r"```|---|\*\*(?!Step\b)", line):
            parts.append(after)
            after = None
        bare = re.sub(r"^\s*(?:[-*+]|\d+\.)?\s*", "", line.replace("**", ""))
        if re.match(r"After that:", bare, re.I):
            after = bare
        elif after is not None:
            after += "\n" + bare
        elif re.match(r"(?:gate\b|step\s+10\b)", bare, re.I):
            parts.append(bare)
    return parts + ([after] if after is not None else [])


def old_ticket_gate(answer):
    """The sentence, or its piece around brackets, that has the tickets themselves waiting on an approval,
    or None.

    Step 10's breakdown is confirmed in the session that makes it; nothing waits on an approval of the tickets. An
    approval is read as the old gate when it is about the tickets ("you approve the tickets", "the tickets wait for
    your approval", "approved by publishing", "`/to-tickets 1` (approval gate)", "the ticket is published once you
    approve it"), no negation sits in its clause ("the tickets need no approval"), its sentence does not set it in
    the session ("you approve the tickets in this session", "(in the same session)"), and its piece of the sentence,
    inside brackets or out, does not name the review, the acceptance verdict, a PR or the merge, which approve each
    ticket later.

    What an approval is about is the first thing named after it in its clause. Failing that, for a verb, the first
    thing named after it in its piece, then the last one named before it; for a noun or a participle, the other way
    round. A thing named right after the tickets to qualify them ("tickets for stories #3") leaves the tickets as
    the last thing named. "It" and "them" stand for the last thing named, or, in a first clause that opens on
    "once", "when", "whenever", "after", "until", "till", "as soon as", "if" or "before", for the first thing named
    after that clause ("once you approve it, the ticket is published"), unless the pronoun is "them" and the tickets
    were the last thing named. So "you approve the breakdown", "you approve the tickets' breakdown", "you approve
    the PRD" and "the design doc is approved" pass.

    It reads the wordings an agent writes in normal work; it does not stop wording made to slip past it. Known
    limits: a negation anywhere in the approval's clause clears it, so "nothing more than your approval of the
    tickets" passes; a colon, a semicolon, a stop or the light answer's dots set a session apart from an approval,
    so "same session: you approve the tickets" fails; "it" stands for the last thing named outside an opening "once"
    or "when" clause, so a later step's "once approved, it ships" fails right after the tickets; a later step named
    in none of the words above reads as step 10; a wording with no approval word ("you publish the tickets") passes;
    and the time it takes grows with the square of a clause's length.
    """
    for part in gate_parts(answer):
        last = None
        pieces = [(piece, CONFIRMATION.search(sentence)) for sentence in SENTENCE.split(part)
                  for piece in PIECE.split(sentence)]
        for piece, confirmed in pieces:
            skipped = confirmed or LATER_STEP.search(piece)
            clauses = CLAUSE.split(piece)
            negated = {number for number, clause in enumerate(clauses) if NEGATION.search(clause)}
            # Each thing the piece names, in order: its clause, its kind, its words and what precedes them.
            named = [(number, found.lastgroup, found.group(), clause[:found.start()])
                     for number, clause in enumerate(clauses) for found in THING.finditer(clause)]
            for index, (number, kind, words, before) in enumerate(named):
                if kind not in ("approval", "pronoun") and not (last == "tickets" and QUALIFIER.search(before)):
                    last = kind
                if (kind != "approval" or skipped or number in negated
                        or words.lower() in ("approved", "approving") and ADJECTIVE.search(before)):
                    continue
                ahead = [(n, k) for n, k, _, _ in named[index + 1:] if k != "approval"]
                in_clause = [k for n, k in ahead if n == number][:1]
                in_piece = [k for _, k in ahead][:1]
                behind = [last] if last else []
                about = (in_clause + (behind + in_piece if STATED.match(words) else in_piece + behind)
                         + [None])[0]
                if about == "pronoun":
                    following = [k for n, k in ahead if n > number and k != "pronoun"][:1]
                    pronoun = next(w.lower() for n, k, w, _ in named[index + 1:] if k == "pronoun")
                    opening = not "".join(clauses[:number]).strip() and LEADING.match(piece)
                    # "Them" right after the tickets stays theirs: "drafts the tickets. Once you approve them,
                    # step 11 starts."
                    kept = pronoun == "them" and last == "tickets"
                    about = following[0] if opening and following and not kept else last
                if about == "tickets":
                    return piece.strip()
    return None


CHECKS = {"old ticket gate": old_ticket_gate}
