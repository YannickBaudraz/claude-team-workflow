"""The harness's own reading of the fixture ticket: it serves the built page and drives it over
HTTP. The sessions never see this file, so what they claim about the page is checked against
something they could not write to. It is not a browser: a session that drives real Chrome can
find more, so a verdict that disagrees with this check is read, not dismissed.

    contract   the ticket's acceptance criteria: one that fails fails the run
    design     what only the interface design asks for: recorded, never failed, because the ticket
               does not ask for it
    escapes    whether an item's name is escaped on the page: the ticket does not ask, so it is
               recorded too, to see what the build and the reviews do with it
    idle       whether the page still answers beside a connection that sends nothing, as Chrome
               opens: a one-thread server waits on it, and the cook's page hangs. Recorded too
"""
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

EMPTY = "Nothing in the pantry yet."
OTHER_UNIT = "Use the same unit as before."
NO_NAME = "Give the item a name."


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def fetch(url, data=None, timeout=5):
    """The page at url after any redirect, whatever its status; "" when nothing answers."""
    form = urllib.parse.urlencode(data).encode() if data is not None else None
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=form), timeout=timeout) as response:
            return response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError):
        return ""


def words(page):
    """The page's text, as a reader sees it."""
    return " ".join(re.sub(r"<[^>]+>", " ", page).split())


def lists(page, name, quantity):
    return bool(re.search(rf"\b{re.escape(name)}\b[\s:–—-]*{re.escape(quantity)}\b", words(page)))


def has_form(page):
    form = re.search(r"<form\b[^>]*>.*?</form>", page, re.S | re.I)
    if not form:
        return False
    tag = form.group(0).split(">")[0]
    return (bool(re.search(r"""action=["']?/items\b""", tag, re.I)) and bool(re.search(r"""method=["']?post\b""", tag, re.I))
            and all(re.search(rf"""name=["']?{field}\b""", form.group(0)) for field in ("name", "quantity")))


def design_facts(page, refused):
    message = refused.find(NO_NAME)
    return {"heading Pantry": bool(re.search(r"<h1\b[^>]*>\s*Pantry\s*</h1>", page, re.I)),
            "labelled fields": all(re.search(rf"<label\b[^>]*>[^<]*{word}", page, re.I) for word in ("Item", "Quantity")),
            "button Add": bool(re.search(r"<button\b[^>]*>\s*Add\s*</button>|<input\b[^>]*value=[\"']?Add\b", page, re.I)),
            "message above the form": -1 < message < refused.lower().find("<form"),
            "keeps what was typed": bool(re.search(r"""value=["']?1kg\b""", refused))}


def answers_beside_an_idle_connection(url, port):
    with socket.create_connection(("127.0.0.1", port), timeout=2):
        return bool(fetch(url + "/", timeout=2))


def walk(port):
    """Every fact, in the order a cook would meet them."""
    url = f"http://127.0.0.1:{port}"
    contract, page = {}, fetch(url + "/")
    contract["empty state"] = EMPTY in page
    contract["form"] = has_form(page)
    fetch(url + "/items", {"name": "rice", "quantity": "2kg"})
    page = fetch(url + "/")
    contract["lists the item"] = lists(page, "rice", "2kg") and EMPTY not in page
    fetch(url + "/items", {"name": "rice", "quantity": "1kg"})
    page = fetch(url + "/")
    contract["adds up"] = lists(page, "rice", "3kg")
    refused = fetch(url + "/items", {"name": "rice", "quantity": "500g"})
    page = fetch(url + "/")
    contract["refuses another unit"] = OTHER_UNIT in refused and lists(page, "rice", "3kg")
    refused = fetch(url + "/items", {"name": "", "quantity": "1kg"})
    contract["refuses an empty name"] = NO_NAME in refused and words(fetch(url + "/")) == words(page)
    design = design_facts(page, refused)
    fetch(url + "/items", {"name": "<b>x</b>", "quantity": "1kg"})
    return {"contract": contract, "design": design, "escapes": "<b>x</b>" not in fetch(url + "/"),
            "idle": answers_beside_an_idle_connection(url, port)}


def serving(port):
    """Whether something listens on port. The probe closes first: a one-thread server would wait on it."""
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", port)) == 0


def check(root, store):
    """Serve the project in root and walk its page, on an empty store."""
    if os.path.exists(store):
        os.unlink(store)
    port = free_port()
    server = subprocess.Popen([sys.executable, "src/pantry.py", "serve", str(port)], cwd=root,
                              env={**os.environ, "PANTRY_STORE": store},
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            if serving(port):
                return walk(port)
            if server.poll() is not None:
                break
            time.sleep(0.1)
        return {"contract": {"serves the page": False}, "design": {}, "escapes": False, "idle": False}
    finally:
        server.terminate()
        server.wait()
