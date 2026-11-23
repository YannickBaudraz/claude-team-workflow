"""The diff from the base branch to the pull request's commit, read through git."""
import subprocess

class GitError(Exception):
    pass


def git(*args):
    """git's output as text; a path git prints that is not UTF-8 keeps its bytes."""
    done = subprocess.run(["git", "-c", "core.quotePath=false", *args], capture_output=True)
    if done.returncode:
        message = done.stderr.decode("utf-8", "replace").strip()
        raise GitError(message or f"git {' '.join(args)} failed")
    return done.stdout.decode("utf-8", "surrogateescape")


def read_file(commit, path):
    """A file's text at a commit, decoded as UTF-8 with anything else replaced; "" when the
    commit has no such file, or it is no file (a submodule)."""
    try:
        done = subprocess.run(["git", "cat-file", "blob", f"{commit}:{path}"], capture_output=True)
    except OSError as error:
        raise GitError(str(error))
    return done.stdout.decode("utf-8", "replace") if done.returncode == 0 else ""


def changed_files(base, head):
    """The files the diff from base to head changes, as dict(old, new): a path, or None for an
    added or deleted file. A rename keeps both paths."""
    fields = git("diff", "--name-status", "-z", "--no-relative", "--find-renames", f"{base}...{head}").split("\0")
    files, index = [], 0
    while index < len(fields) and fields[index]:
        status = fields[index][0]
        if status in "RC":
            old, new = fields[index + 1], fields[index + 2]
            index += 3
        else:
            path = fields[index + 1]
            old, new = (None if status == "A" else path), (None if status == "D" else path)
            index += 2
        files.append(dict(old=old, new=new))
    return files
