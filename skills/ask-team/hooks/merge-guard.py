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
repo commands. For an MCP or plugin tool it refuses any tool whose name says merge, push,
branch protection or ruleset.

It is a filter on the commands the agent runs, not a lock. It cannot see inside a script file
a command runs. The branch rule on the code host still refuses a direct push to the default
branch, but with no approval required it does not stop a PR's merge made under the
developer's login, which the agent uses; only a separate login without merge rights would.

install.sh copies this file to ~/.claude/hooks/, a path that never moves with a branch
checkout, and /project-setup copies it into the project's .claude/hooks/. It exits at once
for a command that names no merge, push, branch rule, default branch or GraphQL call, and
looks for a project map only for a command it would refuse. A command it cannot read is
refused when it names one of those. It refuses with exit code 2 and says why on stderr.

The table of refused and allowed commands is tests/merge-guard/cases.tsv, run in CI.
"""
import json
import os
import re
import shlex
import subprocess
import sys

QUICK = re.compile(r"\bgit\b|\bgh\b|merge|push|protection|ruleset|graphql|refs|contents|default.?branch|alias", re.I)
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
SUBSTITUTION = re.compile(r"\$\(([^()]*)\)|`([^`]*)`|<\(([^()]*)\)")
# What a substitution's output becomes in the command around it: unknown text.
UNKNOWN = "GUARD_UNKNOWN_OUTPUT"
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
GH_BUILTINS = {"agent-task", "alias", "api", "attestation", "auth", "browse", "cache", "codespace", "completion", "config",
               "copilot", "extension", "gist", "gpg-key", "issue", "label", "org", "pr", "preview", "project",
               "release", "repo", "ruleset", "run", "search", "secret", "ssh-key", "status", "variable", "workflow",
               "help", "stack"}
GH_VALUE_OPTIONS = {"-R", "--repo", "--hostname", "-X", "--method", "-H", "--header", "-f", "-F", "--field",
                    "--raw-field", "--input", "-q", "--jq", "-t", "--template", "--cache", "-p", "--preview",
                    "-b", "--branch", "-s", "--source"}


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


def strip_heredocs(command):
    """Drop heredoc bodies: text fed to a command is not a command, unless a shell reads it."""
    lines, kept, ending, run = command.split("\n"), [], None, False
    for line in lines:
        if ending is not None:
            if line.strip() == ending:
                ending = None
            elif run:
                kept.append(line)
            continue
        kept.append(line)
        found = HEREDOC.search(line)
        if found:
            ending = found.group(2)
            run = bool(re.search(r"(^|[\s;&|(])(bash|sh|zsh|dash|ksh|eval|source|\.)(\s|$)", line[:found.start()]))
    return "\n".join(kept)


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
    """The command once assignments and wrappers such as env, sudo or timeout are dropped."""
    while tokens:
        word = os.path.basename(tokens[0]).lower()
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
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


def api_request(arguments):
    """The method, the endpoint, the field values and the files a gh api, curl or PowerShell call sends."""
    method, endpoint, values, files, fields = None, None, [], [], False
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        following = arguments[index + 1] if index + 1 < len(arguments) else ""
        lowered = argument.lower()
        if argument in ("-X", "--method", "--request") or lowered == "-method":
            method, index = following.upper(), index + 2
            continue
        glued = re.match(r"^(?:-X|--method=|--request=)(.+)$", argument)
        if glued:
            method = glued.group(1).upper()
        elif argument in ("--input", "-InFile", "-infile"):
            fields = True
            files.append(following)
            index += 2
            continue
        elif argument.startswith("--input="):
            fields = True
            files.append(argument.split("=", 1)[1])
        elif argument in ("-f", "-F", "--field", "--raw-field", "-d", "--data", "--data-raw", "--data-binary",
                          "--json", "-body", "-Body"):
            fields = True
            values.append(following)
            index += 2
            continue
        elif re.match(r"^(-[fFd].|--(raw-)?field=|--data|--json=)", argument):
            fields = True
            values.append(re.sub(r"^(-[fFd]|--[a-z-]+=)", "", argument))
        elif argument in GH_VALUE_OPTIONS or lowered in ("-uri", "-h", "--header", "-headers"):
            if lowered == "-uri" and endpoint is None:
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
        source = value.split("=", 1)[-1]
        if source.startswith("@"):
            files.append(source[1:])
    if values and any(v in ("-",) for v in values):
        files.append("-")
    return (method or ("POST" if fields else "GET")), (endpoint or ""), values, files


def read_sent(files, directory):
    """The text of the files a request sends, or None when one cannot be read."""
    texts = []
    for name in files:
        if name in ("-", ""):
            return None
        try:
            with open(os.path.join(directory or ".", os.path.expanduser(name)), encoding="utf-8") as sent:
                texts.append(sent.read())
        except OSError:
            return None
    return "\n".join(texts)


def check_api(arguments, directory, redirected=False):
    """A merge, a write to the default branch or a branch-rule change through the code host's API."""
    method, endpoint, values, files = api_request(arguments)
    path = re.sub(r"/+", "/", re.sub(r"/\./", "/", endpoint.split("?", 1)[0]))
    defaults = default_branches(directory)
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
    if re.search(r"git/refs$", path) and writing and any(re.search(rf"refs/heads/({default})$", v) for v in values):
        raise Refused("a write to the default branch's ref through the API")
    if re.search(r"/contents/", path) and method in ("PUT", "DELETE"):
        branch = next((v.split("=", 1)[1] for v in values if v.startswith("branch=")), None)
        if branch is None or branch in defaults:
            raise Refused("a commit to the default branch through the API (contents)")
    if re.search(r"/repos/[^/]+/[^/]+$", "/" + path.lstrip("/")) and method == "PATCH" \
            and any(v.startswith("default_branch=") for v in values):
        raise Refused("a change of the default branch through the API")


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
        check_api(arguments[arguments.index("api") + 1:], directory)


def check_command(command, directory, depth=0, origin=None):
    """Refuse the command when it would be refused and either the session's directory
    (origin) or the directory it acts in belongs to a project set up with the workflow."""
    origin = origin or directory
    if depth > 5:
        raise Refused("commands nested too deep to check")
    command = strip_heredocs(command)
    for found in SUBSTITUTION.finditer(command):
        check_command(next(part for part in found.groups() if part is not None), directory, depth + 1, origin)
    for tokens, piped in simple_commands(SUBSTITUTION.sub(UNKNOWN, command)):
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
        check_api(tokens[1:], directory, redirected="<" in tokens)


def refusal(event):
    """Why the tool call is refused, or None."""
    tool = str(event.get("tool_name") or "")
    given = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
    directory = event.get("cwd") or os.getcwd()
    if tool.startswith("mcp__"):
        return f"the tool {tool}" if MCP_TOOL.search(tool) and workflow_project(directory) else None
    command = given.get("command")
    if not isinstance(command, str) or not QUICK.search(command):
        return None
    try:
        check_command(command, directory)
    except Refused as refused:
        return str(refused)
    except ValueError:
        if workflow_project(directory):
            return "a command naming a merge, a push or a branch rule that could not be read"
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
          "the default branch and changing a branch rule are the developer's acts. Do not rephrase the "
          "command to get around this. Print the exact command for the user to run in a terminal or in shell "
          "mode (!), then wait.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
