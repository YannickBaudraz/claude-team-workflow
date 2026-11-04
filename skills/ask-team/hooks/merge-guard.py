#!/usr/bin/env python3
"""PreToolUse hook: in a project set up with the team workflow, the agent never merges a PR,
never writes to the default branch and never changes a branch rule. Those are the
developer's acts: the developer runs the command the router prints, in a terminal or
in shell mode (!), which no hook sees.

A project is set up with the workflow when its repo has docs/project-map.md, a
"Project map" section in its CLAUDE.md or AGENTS.md, or this hook in .claude/hooks/, as
/project-setup writes them. In any other repo the hook lets everything through: the
guard protects workflow projects only. A command is checked when either the session's directory or
the directory it acts in belongs to such a project.

The deny rules /project-setup writes into the project's .claude/settings.json refuse the
plain spellings; this hook refuses the others: commands inside chains, subshells, `bash -c`
and pipes into a shell, wrapped in env or sudo, behind gh aliases or options, `git -C
<path> push`, a push whose target resolves to the default branch, and merges, writes to the
default branch or branch-rule changes made through `gh api`, curl, PowerShell or gh's own
repo commands. It also refuses publishing a repository security advisory through the API: that
discloses the weakness, so it stays the developer's act, like the merge. For an MCP or plugin
tool it refuses any tool whose name says merge, push, branch protection or ruleset.

It reads a command the way bash does: quotes, escapes, comments, heredocs (a body fed to a shell
is read as a script, any other body only for the substitutions an unquoted delimiter runs),
$'...' strings, case, arithmetic and every $(...), `...`, <(...) and >(...), each checked as a
command of its own. A # or a << inside quotes is text to it, as to the shell. What it cannot
follow, or what depends on values it cannot know, such as a heredoc fed to a shell that expands
variables, it refuses. tests/merge-guard/test_shell_reading.py holds it to that against bash.
A command after a reserved word (if, then, else, elif, while, until, do, !, coproc) is checked like
any other: `if true; then gh pr merge 5; fi` is refused.

An API write (gh api, curl, wget, http, xh, Invoke-RestMethod, Invoke-WebRequest) whose endpoint
holds a variable or a substitution is refused when the endpoint could be one of the paths the
checks protect, with the method and fields the call sends: `curl -X PUT "$URL"` is refused, while
`gh api -X POST repos/o/r/issues/$N/comments` is not, since its readable part rules out every
protected path. The guard reads such an endpoint this way. Its query, scheme and host are dropped,
and so is its base URL: what comes before repos/, orgs/ or graphql, else a variable the rest of
the path follows ("$BASE_URL/api/items"), and GitHub Enterprise Server's api/v3. An endpoint on
localhost, 127.0.0.1 or [::1] is not the code host: its variables are not checked. A variable right
after repos/ is the owner, or owner/repo when a GitHub resource name or nothing follows it
(repos/$GITHUB_REPOSITORY/issues); one in the owner's or the repository's place is a name. A
variable at the path's start, right after the repository or the organization, or after git/refs/
or contents/ may stand for any text; any other stands for text within its own segment
(pulls/$N). A method that comes from a variable counts as each write method. gh's {owner} and
{repo} are names and its {branch} is the current branch. curl's options are read as curl reads
them (-s is a flag, -sX PUT sets the method); the other clients' with gh's list of options.

The ref and branch checks also read a value given as a file (-F ref=@file, --data-urlencode
branch@file, --form 'branch=<file'), and refuse when the file is missing, empty or not a regular
file (stdin, a pipe); a default_branch field is refused whatever its value.

These checks read text: they catch the forms an agent writes in normal work, by mistake or habit.
They do not stop a command crafted to get past them; the review of a change and the developer's
read of the diff do. The guard does not read: a variable that holds more of the path than its
place gives it ("$PR_URL/merge", repos/$REPO/$WHAT), or a query, a fragment or a .. segment; the
shell's brace expansion and curl's URL globs; any URL after curl's first; HTTPie's and xh's
options beyond `http METHOD URL items`; wget's --post-data; a program named through a variable
or quotes ($CLIENT, c''url); the input xargs -I or find -exec puts in a command; a file the same
command line writes before the request reads it. A ref or a branch in a variable (-f branch=$B)
is let through as before: its value is not known before the command runs, and refusing it would
refuse ordinary writes to a feature branch. One in a JSON body (-d '{...}', --input) is read as
before: a ref gets through, a branch is refused as missing. PowerShell's -Body without -Method is
read as a POST, though the cmdlets send a GET, so such a call to an endpoint in a variable is
refused when it need not be.

It is a filter on the commands the agent runs, not a lock. It cannot see inside a script file
a command runs. The branch rule on the code host still refuses a direct push to the default
branch, but with no approval required it does not stop a PR's merge made under the
developer's login, which the agent uses; only a separate login without merge rights would.

install.sh copies this file to ~/.claude/hooks/, a path that never moves with a branch
checkout, and /project-setup copies it into the project's .claude/hooks/. It exits at once
for a command that names no merge, push, branch rule, default branch, advisory or GraphQL call,
and no API client given a method, a body or a file to upload, and looks for a project map only for
a command it would refuse. A command it cannot
read is refused when it names one of those. It refuses with exit code 2 and says why on stderr.

The table of refused and allowed commands is tests/merge-guard/cases.tsv, run in CI.
"""
import json
import os
import re
import shlex
import subprocess
import sys

QUICK = re.compile(r"\bgit\b|\bgh\b|merge|push|protection|ruleset|graphql|refs|contents|default.?branch|alias|advisor", re.I)
PUSH_SETTINGS = r"(?i)(alias\.|remote\..*\.push=|branch\..*\.merge=|push\.default=)"
GIT_BUILTINS = {"add", "am", "apply", "archive", "bisect", "blame", "branch", "bundle", "cat-file", "checkout",
                "cherry", "cherry-pick", "clean", "clone", "commit", "config", "describe", "diff", "fetch",
                "for-each-ref", "format-patch", "fsck", "gc", "grep", "init", "log", "ls-files", "ls-remote",
                "ls-tree", "merge", "merge-base", "mv", "notes", "pull", "push", "range-diff", "rebase", "reflog",
                "remote", "reset", "restore", "rev-list", "rev-parse", "revert", "rm", "shortlog", "show",
                "show-ref", "sparse-checkout", "stash", "status", "submodule", "subtree", "switch", "symbolic-ref",
                "tag", "update-index", "update-ref", "worktree", "help", "version"}
MCP_TOOL = re.compile(r"merge|push|branch_?protection|ruleset", re.I)
DEFAULT_NAMES = {"main", "master"}
WRAPPERS = {"env", "command", "nohup", "time", "exec", "builtin", "nice", "stdbuf", "setsid", "ionice", "chronic",
            "nohup", "flock", "xargs", "timeout", "unbuffer", "caffeinate"}
# Options of the wrappers that take a value, so the value is not read as the wrapped command.
WRAPPER_VALUES = {"env": {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"}, "nice": {"-n", "--adjustment"},
                  "timeout": {"-s", "--signal", "-k", "--kill-after"}, "stdbuf": {"-i", "-o", "-e"},
                  "ionice": {"-c", "-n", "-p"}, "flock": {"-w", "-E", "--timeout", "--conflict-exit-code"},
                  "xargs": {"-n", "-L", "-P", "-I", "-d", "-a", "-s", "-E", "--max-args", "--max-procs",
                            "--delimiter", "--arg-file", "--replace"}}
SUDO_VALUES = {"-u", "-g", "-C", "-h", "-p", "-r", "-t", "-U", "-D", "-R", "--user", "--group"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "fish", "pwsh", "powershell"}
SEPARATORS = {"&&", "||", ";", "|", "&", "(", ")", ";;", "|&", "{", "}"}
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
API_CLIENTS = {"curl", "wget", "http", "https", "xh", "invoke-restmethod", "irm", "invoke-webrequest", "iwr"}
GRAPHQL_WRITES = re.compile(
    r"\b(mergePullRequest|enablePullRequestAutoMerge|enqueuePullRequest|mergeBranch|createCommitOnBranch|updateRefs?"
    r"|deleteRef|updateRepository|(create|update|delete)BranchProtectionRule|(create|update|delete)RepositoryRuleset)\b")
# What a substitution's output becomes in the command around it: unknown text.
UNKNOWN = "GUARD_UNKNOWN_OUTPUT"
# A heredoc's delimiter after <<: a plain word, or one quoted whole. Anything else is read as code.
DELIMITER = re.compile(r"""(-?)[ \t]*(?:'([A-Za-z0-9_.-]+)'|"([A-Za-z0-9_.-]+)"|\\?([A-Za-z0-9_.-]+))(?=[\s;&|()<>]|$)""")
SHELL_READS = re.compile(r"(^|[\s;&|(])(bash|sh|zsh|dash|ksh|eval|source|\.)(\s|$)")
# Where a word ends, so a # after one of these begins a comment.
WORD_BREAKS = set(" \t\n;&|()<>")
GH_BUILTINS = {"agent-task", "alias", "api", "attestation", "auth", "browse", "cache", "codespace", "completion", "config",
               "copilot", "extension", "gist", "gpg-key", "issue", "label", "org", "pr", "preview", "project",
               "release", "repo", "ruleset", "run", "search", "secret", "ssh-key", "status", "variable", "workflow",
               "help", "stack"}
GH_VALUE_OPTIONS = {"-R", "--repo", "--hostname", "-X", "--method", "-H", "--header", "-f", "-F", "--field",
                    "--raw-field", "--input", "-q", "--jq", "-t", "--template", "--cache", "-p", "--preview",
                    "-b", "--branch", "-s", "--source"}
# Words bash reads as reserved at a command's start: the command after them is checked as any other.
RESERVED = {"if", "then", "else", "elif", "while", "until", "do", "!", "coproc"}
# The API clients and the signs of a write, for the quick filter: a command naming one of them and
# giving a method, a body or a file to upload is checked even when it names nothing else the guard
# looks for. A download such as `curl -fsSL URL | sh` gives none of them and stays out, as before.
API_CALL = re.compile(r"\b(curl|wget|xh|invoke-restmethod|irm|invoke-webrequest|iwr)\b|(^|[\s;&|(])https?(\s|$)", re.I)
WRITE_SIGN = re.compile(r"""(?<![^\s'"])(-[A-Za-z]*[XdFT]|--(request|method|data|form|json|upload-file|post))"""
                        r"""|(?i:(?<![^\s'"])-(method|body|infile)\b)|\b(PUT|POST|PATCH|DELETE)\b""")
# An endpoint on this machine: a variable in its path cannot hide one of the code host's paths.
LOCAL_HOST = re.compile(r"^[a-z][\w+.-]*://(localhost|127\.0\.0\.1|\[::1\])([:/]|$)", re.I)
# Text whose value the guard cannot know: a substitution's output, a shell or PowerShell variable.
UNREADABLE = re.compile(rf"{UNKNOWN}|\$\{{[^}}]*\}}|\$(env:)?\w+|\$[@*#?!$-]")
# curl's short options that take a value; every other one is a flag (-s, -f, -L).
CURL_SHORT_VALUES = set("dFHXuoAebcwxUEmrCDTKYyztQP")
CURL_LONG_VALUES = {
    "--request", "--data", "--data-raw", "--data-binary", "--data-ascii", "--data-urlencode", "--json", "--form",
    "--form-string", "--header", "--upload-file", "--config", "--expand-data", "--variable", "--url", "--user",
    "--output", "--user-agent", "--referer", "--cookie", "--cookie-jar", "--write-out", "--proxy", "--cert",
    "--cacert", "--capath", "--key", "--oauth2-bearer", "--max-time", "--connect-timeout", "--retry", "--retry-delay",
    "--retry-max-time", "--dump-header", "--resolve", "--connect-to", "--limit-rate", "--output-dir", "--range",
    "--continue-at", "--unix-socket", "--netrc-file", "--trace", "--trace-ascii", "--stderr", "--url-query",
    "--max-redirs", "--proto", "--interface", "--aws-sigv4", "--noproxy", "--proxy-user"}
# The curl options api_request reads; the others, with their values, say nothing about what is sent where.
CURL_READ = {"-X", "--request", "-d", "--data", "--data-raw", "--data-binary", "--data-ascii", "--data-urlencode",
             "--json", "--form", "--form-string", "-T", "--upload-file", "-K", "--config", "--expand-data",
             "--variable", "--url", "-G", "--get"}
# The paths the checks in check_path protect: {} stands for a name, * for any text. An endpoint the
# guard cannot read is checked as each of these it could be, with the fields the call sends.
PROTECTED = ("repos/{}/{}/pulls/{}/merge", "repos/{}/{}/merges", "repos/{}/{}/merge-upstream",
             "repos/{}/{}/branches/{}/protection", "repos/{}/{}/branches/{}/protection/*", "repos/{}/{}/rulesets",
             "repos/{}/{}/rulesets/*", "orgs/{}/rulesets", "orgs/{}/rulesets/*", "repos/{}/{}/git/refs",
             "repos/{}/{}/contents/*", "repos/{}/{}", "repos/{}/{}/security-advisories/{}", "graphql")
# What follows owner/repo in GitHub's repository endpoints: a variable right before one of them is
# read as owner/repo, as $GITHUB_REPOSITORY is.
REPO_RESOURCES = {
    "actions", "activity", "assignees", "attestations", "autolinks", "automated-security-fixes", "branches",
    "check-runs", "check-suites", "code-scanning", "code-security-configuration", "codeowners", "codespaces",
    "collaborators", "comments", "commits", "community", "compare", "contents", "contributors", "dependabot",
    "dependency-graph", "deployments", "dispatches", "environments", "events", "forks", "generate", "git", "hooks",
    "import", "immutable-releases", "installation", "interaction-limits", "invitations", "issues", "keys", "labels",
    "languages", "lfs", "license", "merge-upstream", "merges", "milestones", "notifications", "pages",
    "private-vulnerability-reporting", "projects", "properties", "pulls", "readme", "releases", "rules", "rulesets",
    "secret-scanning", "security-advisories", "stargazers", "stats", "statuses", "subscribers", "subscription",
    "tags", "tarball", "teams", "topics", "traffic", "transfer", "vulnerability-alerts", "zipball"}


class Refused(Exception):
    pass


def git(directory, *arguments):
    try:
        done = subprocess.run(["git", "-C", directory or ".", *arguments], capture_output=True, text=True, timeout=5)
        return done.stdout.strip() if done.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def workflow_project(directory):
    """Whether the repo holding this directory was set up with the workflow."""
    top = git(directory, "rev-parse", "--show-toplevel")
    if not top:
        return False
    if any(os.path.exists(os.path.join(top, *path)) for path in
           (("docs", "project-map.md"), (".claude", "hooks", "merge-guard.py"))):
        return True
    for name in ("CLAUDE.md", "AGENTS.md"):
        try:
            with open(os.path.join(top, name), encoding="utf-8") as text:
                if re.search(r"^#{1,3}\s+Project map\b", text.read(), re.M):
                    return True
        except OSError:
            continue
    return False


def default_branches(directory):
    names = set(DEFAULT_NAMES)
    head = git(directory, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    if head:
        names.add(head.split("/", 1)[-1])
    return names


# The escapes of a $'...' string, as bash reads them; \NNN, \xHH, \uHHHH and \cX are handled apart.
ANSI_ESCAPES = {"a": "\a", "b": "\b", "e": "\x1b", "E": "\x1b", "f": "\f", "n": "\n", "r": "\r", "t": "\t",
                "v": "\v", "\\": "\\", "'": "'", '"': '"', "?": "?"}
ANSI_CODES = re.compile(r"([0-7]{1,3})|x([0-9A-Fa-f]{1,2})|u([0-9A-Fa-f]{1,4})|U([0-9A-Fa-f]{1,8})")
# Contexts in which the shell reads commands, so a # at a word's start begins a comment and << a heredoc.
COMMAND_CONTEXTS = (None, "$(", "(", "case")
CASE, ESAC = (re.compile(rf"{word}(?=[\s;&|()<>]|$)") for word in ("case", "esac"))


def ansi_value(body):
    """The text a $'...' string stands for."""
    out, i = [], 0
    while i < len(body):
        if body[i] != "\\" or i + 1 == len(body):
            out.append(body[i])
            i += 1
            continue
        code = ANSI_CODES.match(body, i + 1)
        if body[i + 1] in ANSI_ESCAPES:
            out.append(ANSI_ESCAPES[body[i + 1]])
            i += 2
        elif code:
            octal, *hexes = code.groups()
            value = int(octal, 8) if octal else int(next(h for h in hexes if h), 16)
            out.append(chr(value) if value < 0x110000 else "?")
            i = code.end()
        elif body[i + 1] == "c" and i + 2 < len(body):
            out.append(chr(ord(body[i + 2]) & 0x1F))
            i += 3
        else:
            out.append(body[i:i + 2])
            i += 2
    return "".join(out)


def backtick_inner(text):
    """What a `...` substitution runs: inside backticks, \\` \\$ and \\\\ stand for the character."""
    return re.sub(r"\\([`$\\])", r"\1", text)


def expands_anything(body):
    """Whether an unquoted heredoc body holds a $ expansion or a backtick, whose value the guard cannot know."""
    i = 0
    while i < len(body):
        if body[i] == "\\":
            i += 2
            continue
        if body[i] == "`" or re.match(r"\$[A-Za-z_{(0-9?#@*!$-]", body[i:i + 2]):
            return True
        i += 1
    return False


def expanded_body(body):
    """A heredoc body whose delimiter is unquoted, as the shell hands it on: \\$ \\` and \\\\ stand for
    the character, and a backslash before a line break joins the lines."""
    return re.sub(r"\\\n", "", re.sub(r"\\([`$\\])", r"\1", body))


def shell_code(command, body=False):
    """The command as the shell reads it, ready for the lexer, and the text of every command
    substitution in it: $(...), `...`, <(...) and >(...), each replaced in the code by what its
    output stands for (UNKNOWN), and each to be checked as a command of its own.

    In the code, comments are dropped; a heredoc body that a shell reads is kept and read as a
    script of its own; any other body is dropped, but the substitutions the shell runs in it when
    its delimiter is unquoted are kept for checking; a $'...' string becomes its value.

    Quotes, escapes, backticks, $(...), (...), $((...)), ((...)), ${...} and case ... esac are
    followed, so a #, a << or a quote means there what it means to the shell. Text this reading
    cannot follow (an unclosed quote or bracket, a heredoc inside backticks, an unusual delimiter)
    raises ValueError, which refuses the command in a workflow project: guessing could hide one.

    With body=True, the text is a heredoc body whose delimiter is unquoted: the shell reads it as
    it reads a double-quoted string in which a double quote is plain text."""
    out, stack, pending, found = [], [("body", None, None)] if body else [], [], []
    i, n, line_start, word_start = 0, len(command), 0, True

    def open_substitution(kind, width):
        nonlocal i, word_start
        stack.append((kind, len(out), i + width))
        i, word_start = i + width, kind != "`"

    def close_substitution(width):
        nonlocal i, word_start
        kind, at, source = stack.pop()
        text = command[source:i]
        found.append(backtick_inner(text) if kind == "`" else text)
        del out[at:]
        out.append(UNKNOWN)
        i, word_start = i + width, False

    while i < n:
        c, top = command[i], (stack[-1][0] if stack else None)
        if top == "'":
            stack.pop() if c == "'" else None
            out.append(c)
            i += 1
            continue
        if c == "\\" and i + 1 < n:
            pair = command[i:i + 2]
            out.append(pair)
            word_start = word_start if pair == "\\\n" else False
            i += 2
            continue
        if top == "`":
            if command.startswith("<<", i):
                raise ValueError("a heredoc inside backticks")
            if c == "`":
                close_substitution(1)
            else:
                out.append(c)
                i += 1
            continue
        if top in ('"', "body"):
            if c == '"' and top == '"':
                stack.pop()
            elif c == "`":
                open_substitution("`", 1)
                continue
            elif command.startswith("$((", i):
                stack.append(("((", None, None))
                out.append("$((")
                i += 3
                continue
            elif command.startswith("$(", i):
                open_substitution("$(", 2)
                continue
            elif command.startswith("${", i):
                stack.append(("${", None, None))
                out.append("${")
                i += 2
                continue
            out.append(c)
            i += 1
            continue
        # Arithmetic, $((...)) or ((...)), and the brackets inside it: no commands, no comments.
        if top in ("((", "a("):
            if top == "((" and command.startswith("))", i) or top == "a(" and c == ")":
                stack.pop()
                out.append(command[i:i + 2] if top == "((" else c)
                i += 2 if top == "((" else 1
                continue
            if c in "'\"":
                stack.append((c, None, None))
            elif c == "`":
                open_substitution("`", 1)
                continue
            elif command.startswith("$(", i) and not command.startswith("$((", i):
                open_substitution("$(", 2)
                continue
            elif command.startswith("${", i):
                stack.append(("${", None, None))
                out.append("${")
                i += 2
                continue
            elif c == "(":
                stack.append(("a(", None, None))
            out.append(c)
            i += 1
            continue
        commands = top in COMMAND_CONTEXTS
        if c == "#" and commands and word_start:
            end = command.find("\n", i)
            i = n if end == -1 else end
            continue
        if command.startswith("$'", i):
            j = i + 2
            while j < n and command[j] != "'":
                j += 2 if command[j] == "\\" else 1
            if j >= n:
                raise ValueError("an unclosed $'...' string")
            out.append(shlex.quote(ansi_value(command[i + 2:j])))
            i, word_start = j + 1, False
            continue
        if commands and command.startswith("<<", i) and not command.startswith("<<<", i) \
                and not (i and command[i - 1] == "<"):
            heredoc = DELIMITER.match(command, i + 2)
            if not heredoc:
                raise ValueError("a heredoc delimiter the guard cannot read")
            quoted = heredoc.group(2) or heredoc.group(3) or command[heredoc.start(4) - 1] == "\\"
            pending.append((next(g for g in heredoc.groups()[1:] if g), heredoc.group(1) == "-",
                            bool(SHELL_READS.search(command[line_start:i])), not quoted))
            out.append(command[i:heredoc.end()])
            i, word_start = heredoc.end(), False
            continue
        if c == "\n":
            out.append(c)
            i += 1
            for delimiter, tabs, shell, expands in pending:
                lines = []
                while i < n:
                    end = command.find("\n", i)
                    line = command[i:n if end == -1 else end]
                    i = n if end == -1 else end + 1
                    if (line.lstrip("\t") if tabs else line) == delimiter:
                        break
                    lines.append(line + "\n")
                text = "".join(lines)
                # An unquoted delimiter: the shell runs the body's substitutions before anything reads
                # it, and hands it on with each replaced by its output and its escapes taken. What a shell
                # then reads depends on values the guard cannot know, as with eval "$x".
                if expands:
                    if shell and expands_anything(text):
                        raise ValueError("a heredoc read by a shell, holding values the guard cannot know")
                    text, inner = shell_code(text, body=True)
                    text = expanded_body(text)
                    found.extend(inner)
                if shell:
                    code, inner = shell_code(text)
                    out.append(code)
                    found.extend(inner)
            pending, line_start, word_start = [], i, True
            continue
        if commands and word_start and CASE.match(command, i):
            stack.append(("case", None, None))
            out.append("case")
            i, word_start = i + 4, False
            continue
        if top == "case" and word_start and ESAC.match(command, i):
            stack.pop()
            out.append("esac")
            i, word_start = i + 4, False
            continue
        if command.startswith("$((", i) or (commands and word_start and command.startswith("((", i)):
            opener = "$((" if c == "$" else "(("
            stack.append(("((", None, None))
            out.append(opener)
            i, word_start = i + len(opener), False
            continue
        if command.startswith("$(", i) or command.startswith("<(", i) or command.startswith(">(", i):
            open_substitution("$(", 2)
            continue
        if c == "`":
            open_substitution("`", 1)
            continue
        if c == ")" and top == "$(":
            close_substitution(1)
            continue
        # Inside "${...}", a single quote is plain text to the shell.
        if c in "'\"" and not (c == "'" and top == "${" and any(frame[0] == '"' for frame in stack)):
            stack.append((c, None, None))
        elif command.startswith("${", i):
            stack.append(("${", None, None))
            out.append("${")
            i, word_start = i + 2, False
            continue
        elif c == "(":
            stack.append(("(", None, None))
        elif c == ")" and top == "(":
            stack.pop()
        elif c == "}" and top == "${":
            stack.pop()
        out.append(c)
        word_start = c in WORD_BREAKS
        i += 1
    if body and stack and stack[-1][0] == "body":
        stack.pop()
    if stack:
        raise ValueError(f"an unclosed {stack[-1][0]}")
    return "".join(out), found


def simple_commands(command):
    """The command's simple commands, as token lists, split at every operator. Each item is
    (tokens, piped): piped says the command reads the previous one's output."""
    lexer = shlex.shlex(command.replace("\\\n", "").replace("\n", " ; "), posix=True, punctuation_chars=";&|()<>")
    lexer.whitespace_split = True
    lexer.commenters = ""
    current, piped = [], False
    for token in lexer:
        if token in SEPARATORS or set(token) <= set(";&|()"):
            if current:
                yield current, piped
            current, piped = [], token in ("|", "|&")
        else:
            current.append(token)
    if current:
        yield current, piped


def unwrap(tokens):
    """The command once reserved words such as then or do, assignments and wrappers such as env, sudo
    or timeout are dropped."""
    while tokens:
        word = os.path.basename(tokens[0]).lower()
        if tokens[0] in RESERVED or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
            tokens = tokens[1:]
        elif word in WRAPPERS:
            values = WRAPPER_VALUES.get(word, set())
            tokens = tokens[1:]
            while tokens and (tokens[0].startswith("-") or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0])):
                tokens = tokens[2:] if tokens[0] in values else tokens[1:]
            if word == "timeout" and tokens:
                tokens = tokens[1:]
            if word == "flock" and tokens:
                tokens = tokens[1:]
            if word == "xargs" and tokens:
                tokens = tokens + [UNKNOWN]
        elif word in ("sudo", "doas"):
            tokens = tokens[1:]
            while tokens and tokens[0].startswith("-"):
                tokens = tokens[2:] if tokens[0] in SUDO_VALUES else tokens[1:]
        elif word == "start-process":
            program = next((t for t in tokens[1:] if not t.startswith("-")), "")
            listed = tokens[tokens.index("-ArgumentList") + 1:] if "-ArgumentList" in tokens else []
            tokens = [program] + [part for item in listed for part in item.replace("'", "").split(",") if part]
        else:
            break
    return tokens


def branch_name(ref, directory):
    ref = ref.lstrip("+")
    if ref in ("HEAD", "@") or ref.startswith("HEAD~") or ref.startswith("HEAD^"):
        ref = git(directory, "rev-parse", "--abbrev-ref", "HEAD")
    return re.sub(r"^(refs/)?heads/", "", ref)


def resolved_targets(arguments, directory):
    """The remote branches the push would update, as git itself resolves them, or None when
    git cannot tell without the remote (offline, no access)."""
    try:
        done = subprocess.run(["git", "-C", directory or ".", "push", "--dry-run", "--porcelain", *arguments],
                              capture_output=True, text=True, timeout=8,
                              env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "true", "SSH_ASKPASS": "true"})
    except (OSError, subprocess.SubprocessError):
        return None
    lines = [line.split("\t") for line in done.stdout.splitlines() if "\t" in line]
    targets = [fields[1].split(":", 1)[-1] for fields in lines if len(fields) > 1 and ":" in fields[1]]
    return targets if targets or done.returncode == 0 else None


def check_push(arguments, directory):
    positional, deleting, skip = [], False, False
    for argument in arguments:
        if skip:
            skip = False
        elif argument in ("--all", "--mirror", "--branches"):
            raise Refused(f"`git push {argument}` pushes every branch, the default branch included")
        elif argument in ("-d", "--delete"):
            deleting = True
        elif argument in ("--repo", "-o", "--push-option", "--receive-pack", "--exec"):
            skip = True
        elif not argument.startswith("-"):
            positional.append(argument)
    defaults = default_branches(directory)
    refspecs = positional[1:]
    for spec in refspecs:
        if UNKNOWN in spec or any(mark in spec for mark in "$`{}"):
            raise Refused("a push whose target the guard cannot read")
        if "*" in spec or spec.lstrip("+") == ":":
            raise Refused("a push of every matching branch, the default branch included")
    if any(UNKNOWN in p or "$" in p for p in positional[:1]):
        raise Refused("a push whose remote the guard cannot read")
    targets = resolved_targets(arguments, directory)
    if targets is not None:
        for target in targets:
            if re.sub(r"^refs/heads/", "", target) in defaults:
                raise Refused(f"`git push` updates the default branch ({target})")
    if not refspecs and git(directory, "config", "--get", "push.default") == "matching":
        raise Refused("`git push` with push.default=matching pushes the default branch")
    remote = positional[0] if positional else "origin"
    for mapping in git(directory, "config", "--get-all", f"remote.{remote}.push").splitlines():
        if branch_name(mapping.split(":", 1)[-1], directory) in defaults or "*" in mapping:
            raise Refused(f"remote.{remote}.push maps this push onto the default branch")
    if not refspecs:
        current = git(directory, "rev-parse", "--abbrev-ref", "HEAD")
        upstream = git(directory, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").split("/", 1)[-1]
        if current in defaults or upstream in defaults:
            raise Refused(f"`git push` from {current} pushes the default branch")
        return
    for spec in refspecs:
        target = spec[1:] if spec.startswith(":") else spec.split(":", 1)[-1]
        if target == "@{u}" or target.endswith("@{upstream}"):
            target = git(directory, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").split("/", 1)[-1]
        name = branch_name(target, directory)
        if name in defaults:
            raise Refused(f"`git push` {'deletes' if deleting or spec.startswith(':') else 'updates'} the default branch ({name})")


def check_git(tokens, directory):
    arguments = tokens[1:]
    while arguments and arguments[0].startswith("-"):
        option = arguments.pop(0)
        if option == "-C" and arguments:
            directory = os.path.join(directory or ".", os.path.expanduser(arguments.pop(0)))
        elif option.startswith("--config-env"):
            raise Refused("git settings taken from the environment for this one command")
        elif option in ("-c", "--git-dir", "--work-tree", "--namespace") and arguments:
            value = arguments.pop(0)
            if option == "-c" and re.match(PUSH_SETTINGS, value):
                raise Refused("git settings given for this one command that change where it pushes")
    if not arguments:
        return
    if UNKNOWN in arguments[0] or any(mark in arguments[0] for mark in "$`{}"):
        raise Refused("a git command the guard cannot read")
    expansion = git(directory, "config", "--get", f"alias.{arguments[0]}") if re.match(r"^[\w-]+$", arguments[0]) \
        and arguments[0] not in GIT_BUILTINS else ""
    if expansion and expansion.lstrip("!").split()[0:1] != [arguments[0]]:
        rest = " ".join(shlex.quote(a) for a in arguments[1:])
        check_command((expansion[1:] if expansion.startswith("!") else "git " + expansion) + " " + rest, directory)
        return
    if arguments[0] == "push":
        check_push(arguments[1:], directory)
    elif arguments[0] == "subtree" and "push" in arguments[1:]:
        check_push(arguments[arguments.index("push") + 1:], directory)
    elif arguments[0] in ("send-pack", "http-push", "receive-pack"):
        raise Refused(f"`git {arguments[0]}`, which pushes")
    elif arguments[0] == "config":
        settings = [a for a in arguments[1:] if not a.startswith("-")]
        if settings and re.match(PUSH_SETTINGS, settings[0] + "=") and len(settings) > 1:
            raise Refused("a git setting that changes where a push goes")
        if settings and re.match(r"(?i)alias\.", settings[0]) and len(settings) > 1 \
                and (settings[1].startswith("!") or re.search(r"\bpush\b|send-pack", settings[1])):
            raise Refused("a git alias that runs a shell or pushes")
    elif arguments[0] in ("rebase", "bisect", "submodule"):
        for flag in ("-x", "--exec", "run", "foreach"):
            if flag in arguments[1:]:
                index = arguments.index(flag)
                for part in arguments[index + 1:]:
                    if not part.startswith("-"):
                        check_command(part if flag != "run" else " ".join(arguments[index + 1:]), directory)
                        break


def curl_arguments(arguments):
    """curl's arguments with each short option apart (-sX PUT is -s -X PUT, -dx is -d x), -F spelled
    --form, and every option api_request does not read dropped with its value, so that a flag such
    as -s or -f is never read as taking the next word."""
    out, index = [], 0
    while index < len(arguments):
        argument = arguments[index]
        following = arguments[index + 1] if index + 1 < len(arguments) else ""
        index += 1
        if argument.startswith("--"):
            name, glued, value = argument.partition("=")
            takes = name in CURL_LONG_VALUES and not glued
            out += ([name, value if glued else following] if name in CURL_LONG_VALUES else [name]) \
                if name in CURL_READ else []
            index += 1 if takes else 0
        elif argument.startswith("-") and len(argument) > 1:
            for at, letter in enumerate(argument[1:], 1):
                if letter in CURL_SHORT_VALUES:
                    value = argument[at + 1:] or following
                    index += 0 if argument[at + 1:] else 1
                    option = "--form" if letter == "F" else "-" + letter
                    out += [option, value] if option in CURL_READ else []
                    break
                if "-" + letter in CURL_READ:
                    out.append("-" + letter)
        else:
            out.append(argument)
    return out


def api_request(arguments, client=""):
    """The method, the endpoint, the field values and the files a gh api, curl or PowerShell call sends.
    A file sent as a field's value is a (name, path) pair, so its text is read as that field's."""
    method, endpoint, values, files, fields, get = None, None, [], [], False, False
    if client == "curl":
        arguments = curl_arguments(arguments)
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        following = arguments[index + 1] if index + 1 < len(arguments) else ""
        lowered = argument.lower()
        if argument in ("-G", "--get"):  # curl sends the data as the query of a GET
            get, index = True, index + 1
            continue
        if argument in ("-X", "--method", "--request") or lowered == "-method":
            method, index = following.upper(), index + 2
            continue
        glued = re.match(r"^(?:-X|--method=|--request=)(.+)$", argument)
        if glued:
            method = glued.group(1).upper()
        elif argument in ("--input", "-InFile", "-infile", "-T", "--upload-file"):
            fields = True
            if argument in ("-T", "--upload-file") and method is None:
                method = "PUT"  # curl's default for an upload
            files.append(following)
            index += 2
            continue
        elif argument.startswith("--input="):
            fields = True
            files.append(argument.split("=", 1)[1])
        elif argument in ("--expand-data", "--variable", "-K", "--config"):
            # curl builds what it sends from variables or reads its options from a file: unreadable.
            fields = True
            files.append("-")
            index += 2
            continue
        elif argument == "--data-urlencode":
            # curl's forms: content, =content, name=content, @file, name@file.
            fields = True
            named_file = re.match(r"^([^=@]*)@(.*)$", following)
            if named_file:
                files.append((named_file.group(1), named_file.group(2)))
            else:
                values.append(following)
            index += 2
            continue
        elif argument == "--form":
            # curl's name=<file sends the file's text as the value; only --form reads < so.
            fields = True
            from_file = re.match(r"^([^=]*)=<(.*)$", following)
            if from_file:
                files.append((from_file.group(1), from_file.group(2)))
            else:
                values.append(following)
            index += 2
            continue
        elif argument in ("-f", "-F", "--field", "--raw-field", "-d", "--data", "--data-raw", "--data-binary",
                          "--data-ascii", "--form-string", "--json", "-body", "-Body"):
            fields = True
            values.append(following)
            index += 2
            continue
        elif re.match(r"^(-[fFd].|--(raw-)?field=|--data|--json=)", argument):
            fields = True
            values.append(re.sub(r"^(-[fFd]|--[a-z-]+=)", "", argument))
        elif argument in GH_VALUE_OPTIONS or lowered in ("-uri", "-h", "--header", "-headers"):
            if lowered == "-uri":
                endpoint = following
            index += 2
            continue
        elif not argument.startswith("-") and argument.upper() in WRITE_METHODS | {"GET"} and index == 0:
            method = argument.upper()
        elif not argument.startswith("-"):
            if endpoint is None or (re.search(r"://|^/|^repos/|graphql$", argument) and
                                    not re.search(r"://|^/|^repos/|graphql$", endpoint)):
                endpoint = argument
        index += 1
    for value in values:
        name, _, source = value.partition("=") if "=" in value else ("", "", value)
        if source.startswith("@"):
            files.append((name, source[1:]) if name else source[1:])
    if values and any(v in ("-",) for v in values):
        files.append("-")
    return (method or ("POST" if fields and not get else "GET")), (endpoint or ""), values, files


def read_file(name, directory):
    """A file's text, or None when the guard cannot read it before the command runs: stdin, a file
    that is missing or that is not a regular file (a pipe, a device)."""
    path = os.path.join(directory or ".", os.path.expanduser(name))
    if name in ("-", "") or not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as sent:
            return sent.read()
    except (OSError, ValueError):
        return None


def read_sent(files, directory):
    """The text of the files a request sends, or None when one cannot be read."""
    texts = []
    for name in files:
        field, name = name if isinstance(name, tuple) else ("", name)
        text = read_file(name, directory)
        if text is None:
            return None
        texts.append(f"{field}={text}" if field else text)
    return "\n".join(texts)


def field_values(name, values, files, directory):
    """The values a request sends for one field: given inline (name=value) or as a file it names
    (-F name=@file, --data-urlencode name@file, --form 'name=<file'). A file it cannot read, or
    that holds nothing, gives None."""
    found = [v.split("=", 1)[1] for v in values if v.startswith(name + "=") and not v.startswith(name + "=@")]
    for sent in files:
        if isinstance(sent, tuple) and sent[0] == name:
            text = read_file(sent[1], directory)
            found.append(text.strip() if text and text.strip() else None)
    return found


# What an unreadable stretch of an endpoint may stand for: any text, or text within one segment.
ANY_TEXT, SEGMENT_TEXT = 1, 2


def endpoint_items(endpoint):
    """The endpoint's path as could_be reads it: its characters, and ANY_TEXT or SEGMENT_TEXT for each
    stretch the guard cannot read. The query and the scheme and host are dropped; so is the API's base
    URL: what comes before repos/, orgs/ or graphql, else a variable the rest of the path follows, as
    in "$BASE_URL/api/items", and GitHub Enterprise Server's api/v3. The owner and the repository are
    names, read as o and r: a variable right after repos/ stands for owner/repo when a resource name
    or nothing follows it. A stretch at the path's start, right after the repository or the
    organization, or after git/refs/ or contents/ may stand for any text; any other stands for text
    within its segment."""
    path = re.sub(r"^[A-Za-z][\w+.-]*://[^/]*", "", endpoint.split("?", 1)[0].split("#", 1)[0])
    segments = [s for s in path.split("/") if s not in ("", ".")]
    anchor = next((i for i, s in enumerate(segments) if s in ("repos", "orgs") and i + 1 < len(segments)
                   or s == "graphql" and i + 1 == len(segments)), None)
    if anchor is not None:
        segments = segments[anchor:]
    elif len(segments) > 1 and UNREADABLE.fullmatch(segments[0]):
        segments = segments[1:]
    if anchor is None and segments[:2] == ["api", "v3"]:
        segments = segments[2:]
    if segments[:1] == ["repos"] and len(segments) > 1:
        whole = UNREADABLE.fullmatch(segments[1]) and (len(segments) == 2 or segments[2] in REPO_RESOURCES)
        segments = ["repos", "o", "r"] + segments[2 if whole else 3:]
    elif segments[:1] == ["orgs"]:
        segments = ["orgs", "o"] + segments[2:]
    items = []
    for index, segment in enumerate(segments):
        items += ["/"] if index else []
        wide = index == 0 or segments[:index] in (["repos", "o", "r"], ["orgs", "o"]) \
            or segments[index - 1] == "contents" or segments[max(index - 2, 0):index] == ["git", "refs"]
        at = 0
        for found in UNREADABLE.finditer(segment):
            items += list(segment[at:found.start()]) + [ANY_TEXT if wide else SEGMENT_TEXT]
            at = found.end()
        items += list(segment[at:])
    return items


def could_be(items, template):
    """Whether the path, each of its unreadable stretches filled with some text, can be the template,
    in which {} stands for a name, with no slash, and * for any text."""
    route, at = [], 0
    while at < len(template):  # each wildcard of the template: one character, then any number more
        if template.startswith("{}", at):
            route += ["name", "names"]
            at += 2
        elif template[at] == "*":
            route += ["text", "texts"]
            at += 1
        else:
            route.append(template[at])
            at += 1
    seen, todo = set(), [(0, 0)]
    while todo:
        i, j = todo.pop()
        if (i, j) in seen:
            continue
        seen.add((i, j))
        if i == len(items) and j == len(route):
            return True
        item = items[i] if i < len(items) else ""
        step = route[j] if j < len(route) else ""
        if item in (ANY_TEXT, SEGMENT_TEXT):  # the stretch ends, or gives the template's next character
            todo.append((i + 1, j))
            if step and not (item == SEGMENT_TEXT and step == "/"):
                todo.append((i, j + 1))
        elif step in ("names", "texts"):  # the template's wildcard ends, or takes the path's next character
            todo.append((i, j + 1))
            if item and (step == "texts" or item != "/"):
                todo.append((i + 1, j))
        elif item and step and (item == step or step == "text" or step == "name" and item != "/"):
            todo.append((i + 1, j + 1))
    return False


def check_api(arguments, directory, client="", redirected=False):
    """A merge, a write to the default branch, a branch-rule change or an advisory's publication through
    the code host's API. A method the guard cannot read counts as each write; a write to an endpoint it
    cannot read is checked as each protected path the endpoint could be."""
    method, endpoint, values, files = api_request(arguments, client)
    if client == "gh" and "{branch}" in endpoint + "".join(values):
        # gh fills {branch} with the current branch.
        branch = git(directory, "rev-parse", "--abbrev-ref", "HEAD") or UNKNOWN
        endpoint, values = endpoint.replace("{branch}", branch), [v.replace("{branch}", branch) for v in values]
    methods = sorted(WRITE_METHODS) if UNREADABLE.search(method) else [method]
    path = re.sub(r"/+", "/", re.sub(r"/\./", "/", endpoint.split("?", 1)[0]))
    defaults = default_branches(directory)
    for each in methods:
        check_path(each, path, values, files, directory, redirected, defaults)
    if not UNREADABLE.search(endpoint) or not set(methods) & WRITE_METHODS or LOCAL_HOST.match(endpoint):
        return
    items = endpoint_items(endpoint)
    routes = PROTECTED + tuple(f"repos/{{}}/{{}}/git/refs/heads/{name}" for name in sorted(defaults))
    for route in routes:
        if could_be(items, route):
            example = route.replace("{}", "x").replace("*", "x")
            for each in set(methods) & WRITE_METHODS:
                try:
                    check_path(each, example, values, files, directory, redirected, defaults)
                except Refused as refused:
                    raise Refused(f"an API write whose endpoint the guard cannot read, which could be {refused}") \
                        from None


def check_path(method, path, values, files, directory, redirected, defaults):
    """The checks of check_api on one method and one endpoint path."""
    default = "|".join(map(re.escape, sorted(defaults)))
    if re.search(r"(^|/)graphql$", path):
        sent = read_sent(files, directory)
        body = " ".join(values) + " " + (sent or "")
        if sent is None or redirected or UNKNOWN in body:
            raise Refused("a GraphQL request whose query the guard cannot read; pass the query inline with -f query=")
        if re.search(r"\bmutation\b", body) and GRAPHQL_WRITES.search(body):
            raise Refused("a GraphQL mutation that merges, writes to a branch or changes a branch rule or the default branch")
        return
    writing = method in WRITE_METHODS
    if re.search(r"pulls/[^/\s]+/merge\b", path, re.I) and method != "GET":
        raise Refused("a merge through the API (pulls/<n>/merge)")
    if re.search(r"/merges$", path) and writing:
        raise Refused("a branch merge through the API (/merges)")
    if re.search(r"/merge-upstream$", path) and writing:
        raise Refused("a sync onto a branch through the API (/merge-upstream)")
    if re.search(r"branches/[^/\s]+/protection|/rulesets\b", path) and writing:
        raise Refused("a branch rule change through the API")
    if re.search(rf"git/refs/heads/({default})$", path) and writing:
        raise Refused("a write to the default branch's ref through the API")
    if re.search(r"git/refs$", path) and writing:
        refs = field_values("ref", values, files, directory)
        if None in refs or any(re.search(rf"refs/heads/({default})$", v) for v in values + refs):
            raise Refused("a write to the default branch's ref through the API, or to a ref read from a file "
                          "the guard cannot read")
    if re.search(r"/contents/", path) and method in ("PUT", "DELETE"):
        branches = field_values("branch", values, files, directory)
        if not branches or None in branches or any(b in defaults for b in branches):
            raise Refused("a commit to the default branch through the API (contents), or to a branch read from "
                          "a file the guard cannot read")
    if re.search(r"/repos/[^/]+/[^/]+$", "/" + path.lstrip("/")) and method == "PATCH" \
            and (any(v.startswith("default_branch=") for v in values)
                 or any(isinstance(f, tuple) and f[0] == "default_branch" for f in files)):
        raise Refused("a change of the default branch through the API")
    if re.search(r"security-advisories/[^/\s]+$", path) and writing:
        sent = read_sent(files, directory)
        body = " ".join(values) + " " + (sent or "")
        if sent is None or redirected or UNKNOWN in body or re.search(r"""\bstate\b\W*published\b""", body):
            raise Refused("publishing a security advisory, which discloses the weakness; the developer publishes it")


def gh_words(arguments):
    """gh's subcommand words, with every option and its value dropped."""
    words, skip = [], False
    for argument in arguments:
        if skip:
            skip = False
        elif argument in GH_VALUE_OPTIONS:
            skip = True
        elif not argument.startswith("-"):
            words.append(argument)
    return words


def gh_alias(name):
    try:
        listed = subprocess.run(["gh", "alias", "list"], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return ""
    for line in listed.splitlines():
        alias, _, expansion = line.partition(":")
        if alias.strip() == name:
            return expansion.strip().strip("'\"")
    return ""


def check_gh(tokens, directory, depth, origin):
    arguments = tokens[1:]
    words = gh_words(arguments)
    if not words:
        return
    if words[0] not in GH_BUILTINS:
        expansion = gh_alias(words[0])
        if expansion:
            given = arguments[arguments.index(words[0]) + 1:]
            used = set()
            def fill(match):
                if match.group(1) in ("*", "@"):
                    used.update(range(len(given)))
                    return " ".join(shlex.quote(a) for a in given)
                number = int(match.group(1)) - 1
                used.add(number)
                return shlex.quote(given[number]) if number < len(given) else ""
            body = re.sub(r"\$(\d+|\*|@)", fill, expansion.lstrip("!"))
            rest = " ".join(shlex.quote(a) for i, a in enumerate(given) if i not in used)
            check_command(("" if expansion.startswith("!") else "gh ") + body + " " + rest, directory, depth + 1, origin)
        return
    if words[:2] == ["pr", "merge"]:
        raise Refused("`gh pr merge`")
    if words[:2] == ["stack", "merge"]:
        raise Refused("`gh stack merge`")
    if words[:2] == ["alias", "set"] or words[:2] == ["alias", "import"]:
        if re.search(r"merge|push|\bapi\b|default-branch|repo\s+(sync|create)|\$|--shell|-s\b", " ".join(arguments)):
            raise Refused("a gh alias that merges, pushes, calls the API, runs a shell or takes arguments")
    if words[:2] == ["repo", "edit"] and any(a.startswith("--default-branch") for a in arguments):
        raise Refused("a change of the default branch")
    if words[:2] == ["repo", "create"] and "--push" in arguments:
        raise Refused("`gh repo create --push`, the first push of the default branch")
    if words[:2] == ["repo", "sync"] and len(words) > 2:
        raise Refused("`gh repo sync` onto a branch of a repository on the code host")
    if words[:1] == ["api"]:
        check_api(arguments[arguments.index("api") + 1:], directory, "gh")


def check_command(command, directory, depth=0, origin=None):
    """Refuse the command when it would be refused and either the session's directory
    (origin) or the directory it acts in belongs to a project set up with the workflow."""
    origin = origin or directory
    if depth > 5:
        raise Refused("commands nested too deep to check")
    code, substitutions = shell_code(command)
    for text in substitutions:
        check_command(text, directory, depth + 1, origin)
    for tokens, piped in simple_commands(code):
        settings = [t for t in tokens if re.match(r"^GIT_CONFIG(_COUNT|_KEY_\d+|_VALUE_\d+|_PARAMETERS)?=", t)]
        tokens = unwrap(tokens)
        if not tokens:
            continue
        word = os.path.basename(tokens[0]).lower().lstrip("=")
        if settings and word.startswith("git"):
            tokens = ["git", "-c", "push.default=" + UNKNOWN] + tokens[1:]
        if word.startswith("git-") and word != "git-lfs":
            tokens, word = ["git", word[4:]] + tokens[1:], "git"
        if word in ("cd", "pushd", "set-location") and len(tokens) > 1:
            directory = os.path.join(directory or ".", os.path.expanduser(tokens[-1]))
            continue
        try:
            check_simple(word, tokens, directory, depth, origin, piped)
        except Refused:
            if workflow_project(origin) or workflow_project(target_directory(tokens, directory)):
                raise


def target_directory(tokens, directory):
    """The directory a git command acts in: its -C path, else the current one."""
    if os.path.basename(tokens[0]) == "git" and "-C" in tokens:
        index = tokens.index("-C")
        if index + 1 < len(tokens):
            return os.path.join(directory or ".", os.path.expanduser(tokens[index + 1]))
    return directory


def check_simple(word, tokens, directory, depth, origin, piped):
    options = [t for t in tokens[1:] if t.startswith("-")]
    if UNKNOWN in tokens[0] or tokens[0].startswith("$"):
        if QUICK.search(" ".join(tokens)):
            raise Refused("a command whose program the guard cannot read")
    elif word in SHELLS:
        flag = next((t for t in tokens[1:] if re.match(r"^-[a-zA-Z]*c[a-zA-Z]*$", t) or t.lower() == "-command"), None)
        if "<<<" in tokens:
            given = tokens[tokens.index("<<<") + 1:tokens.index("<<<") + 2]
            check_command(given[0] if given else UNKNOWN, directory, depth + 1, origin)
        if flag:
            index = tokens.index(flag) + 1
            while index < len(tokens) and tokens[index] == "--":
                index += 1
            if index < len(tokens):
                check_command(tokens[index], directory, depth + 1, origin)
        elif (piped or "<" in tokens) and not [t for t in tokens[1:] if not t.startswith("-") and t not in ("<", "<<<")
                                               and not tokens[tokens.index(t) - 1] in ("<", "<<<")]:
            raise Refused("commands fed to a shell from another command or a file")
    elif word in ("eval", "invoke-expression", "iex"):
        text = " ".join(tokens[1:])
        if "$" in text or UNKNOWN in text:
            raise Refused("an eval of text the guard cannot read")
        check_command(text, directory, depth + 1, origin)
    elif word in ("source", "."):
        if piped or "<" in tokens or "<<<" in tokens or any(UNKNOWN in t or "/dev/stdin" in t for t in tokens[1:]):
            raise Refused("commands fed to the shell from another command")
    elif word == "alias" and re.search(r"\b(git|gh)\b.*\b(push|merge|api)\b|\bpush\b|\bmerge\b", " ".join(tokens[1:])):
        raise Refused("a shell alias that pushes or merges")
    elif word == "find" and "-exec" in tokens:
        index = tokens.index("-exec") + 1
        end = next((i for i in range(index, len(tokens)) if tokens[i] in (";", "\\;", "+")), len(tokens))
        check_command(" ".join(shlex.quote(t) for t in tokens[index:end]), directory, depth + 1, origin)
    elif word == "git":
        check_git(tokens, directory)
    elif word == "gh":
        check_gh(tokens, directory, depth, origin)
    elif word in API_CLIENTS:
        check_api(tokens[1:], directory, word if word == "curl" else "", redirected="<" in tokens)


def refusal(event):
    """Why the tool call is refused, or None."""
    tool = str(event.get("tool_name") or "")
    given = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
    directory = event.get("cwd") or os.getcwd()
    if tool.startswith("mcp__"):
        return f"the tool {tool}" if MCP_TOOL.search(tool) and workflow_project(directory) else None
    command = given.get("command")
    if not isinstance(command, str) \
            or not (QUICK.search(command) or API_CALL.search(command) and WRITE_SIGN.search(command)):
        return None
    try:
        check_command(command, directory)
    except Refused as refused:
        return str(refused)
    except ValueError:
        if workflow_project(directory):
            return "a command naming a merge, a push, a branch rule or an API write that could not be read"
    return None


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        event = None
    try:
        if not isinstance(event, dict):
            reason = "a tool call the guard could not read" if workflow_project(os.getcwd()) else None
        else:
            reason = refusal(event)
    except Exception as error:  # a crash refuses in a workflow project and lets the call through elsewhere
        directory = event.get("cwd") if isinstance(event, dict) and event.get("cwd") else os.getcwd()
        reason = f"a tool call the guard failed to check ({type(error).__name__})" if workflow_project(directory) else None
    if reason is None:
        return 0
    print(f"Refused by the team workflow's merge guard: {reason}. In this project, merging a PR, writing to "
          "the default branch, changing a branch rule and publishing a security advisory are the developer's acts. Do not rephrase the "
          "command to get around this. Print the exact command for the user to run in a terminal or in shell "
          "mode (!), then wait.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
