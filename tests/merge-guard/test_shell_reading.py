"""Holds skills/ask-team/hooks/merge-guard.py to bash: every command bash runs, the guard reads.

Each case is a few risky pieces joined at random: comments holding quotes, a << in a comment, in
quotes or in a here-string, heredocs fed to cat or to bash, escaped and nested backticks, $(...),
${...}, $'...', case, arithmetic. Marker commands stand in for a push. bash runs each case in an
empty folder, and its "command not found" lines say which markers it ran. The guard must read
each of those as a command, or refuse the case as one it cannot read. Reading more than bash runs
is allowed: the guard may only err towards refusing.

Run: python3 -m unittest discover tests/merge-guard
"""
import importlib.util
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

# Loading the hook as a module must leave no cached copy beside it.
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.environ.get("MERGE_GUARD", os.path.join(HERE, "..", "..", "skills", "ask-team", "hooks", "merge-guard.py"))
CASES = 1500
PIECES = [
    "{m}", "echo it\\'s", "echo 'it'\"'\"'s'", "# a comment's text", "# see <<EOF", "#{m}", "echo a#b {m}x",
    "echo \\#x", "echo \\ #x {m}", "echo \"a # b\"", "echo '<<EOF'", "echo \"<<EOF\"", "cat <<<EOF",
    "cat <<EOF\n{m}\nEOF", "cat <<'EOF'\n# it's {m}\nEOF", "cat <<-EOF\n\t{m}\n\tEOF", "bash <<EOF\n{m}\nEOF",
    "bash <<'X'\n# it's\n{m}\nX", "x=$({m})", "x=`{m}`", "echo \"`{m}`\"", "echo \"\\`{m}\\`\"", "x=`echo \\`{m}\\``",
    "( {m} )", "{{ {m}; }}", "echo $((1 + 2))", "(( 1 + 2 ))", "echo ${{x:-\"a # b\"}}", "echo ${{#x}}",
    "echo $(echo a) # it's", "x=$(echo a #b\n)", "echo \"multi\nline # it's\"", "true -m \"A\n\n\\`x\\` y\"",
    "true <<EOF # trailing's\n{m}\nEOF", "echo \"$({m})\"", "echo '$({m})'", "echo 'a`{m}`b'", "echo \"a\\\"b # c\"",
    "echo a \\\n#notcomment {m}", "f() {{ {m}; }}; f", "echo $'it\\'s' ; {m}", "case a in a) {m};; esac",
    "cat <<EOF; {m}\nbody's\nEOF", "cat <<A <<B\n{m}\nA\n{m}\nB", "echo $(cat <<EOF\n{m}\nEOF\n)", "x=\"${{y:-$({m})}}\"",
    "echo $'a\\nb' {m}x", "{m} $'x'", "x=$( {m} # it's\n)", "(( x = 1 )) # it's", "echo $(( 16#ff ))",
    "case $x in (a) {m};; b) true;; esac", "x=$(case a in a) {m};; esac)", "cat <<\\EOF\n$({m})\nEOF",
    "cat <<EOF\n$({m}) and it's\nEOF", "cat <<'EOF'\n$({m})\nEOF", "echo \"${{x:-$'y'}}\"", "bash -c '{m}' # it's",
    "echo \"${{x:-'a # b'}}\"", "echo \"${{x:-'}}\"", "echo $(( (1 + 2) * 3 )) ; {m}", "(( (1) )) # it's",
    "echo ${{x:-'a # b'}}", "x=$(echo \")\" ; {m})", "{m} <(echo a)",
]
SEPARATORS = [" ; ", "\n", " && ", " || ", " | ", " "]


def load_guard():
    spec = importlib.util.spec_from_file_location("merge_guard", HOOK)
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    return guard


def cases(count, seed=11):
    rng, number = random.Random(seed), [0]

    def marker(_):
        number[0] += 1
        return f"mark_{number[0]}"
    for _ in range(count):
        pieces = [re.sub(r"\{m\}", marker, piece.replace("{{", "\x01").replace("}}", "\x02"))
                  .replace("\x01", "{").replace("\x02", "}") for piece in rng.choices(PIECES, k=rng.randint(1, 4))]
        command = pieces[0]
        for piece in pieces[1:]:
            command += rng.choice(SEPARATORS) + piece
        yield command


@unittest.skipUnless(shutil.which("bash"), "needs bash")
class ReadsWhatBashRuns(unittest.TestCase):
    def test_every_command_bash_runs_is_read_or_the_case_refused(self):
        guard, seen = load_guard(), []
        check_simple = guard.check_simple

        def recording(word, tokens, *rest):
            seen.append(word)
            return check_simple(word, tokens, *rest)
        guard.check_simple = recording
        guard.workflow_project = lambda directory: False
        folder = tempfile.mkdtemp(prefix="shell-reading-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        missed, refused = [], 0
        for command in cases(CASES):
            done = subprocess.run(["bash", "-c", command], cwd=folder, capture_output=True, text=True,
                                  stdin=subprocess.DEVNULL, timeout=10, env={"PATH": "/usr/bin:/bin"})
            ran = set(re.findall(r"(mark_\d+): command not found", done.stderr))
            seen.clear()
            try:
                guard.check_command(command, folder)
            except ValueError:
                refused += 1
                continue
            if ran - set(seen):
                missed.append((command, sorted(ran - set(seen))))
        self.assertEqual(missed[:5], [], f"{len(missed)} of {CASES} cases ran a command the guard did not read")
        # Refusing is the safe error, but a guard that refused everything would pass the line above.
        self.assertLess(refused, CASES // 10)


if __name__ == "__main__":
    unittest.main()
