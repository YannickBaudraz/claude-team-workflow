"""Pantry: what is in the kitchen."""
import json
import sys
from pathlib import Path

STORE = Path.home() / ".pantry.json"


def load():
    return json.loads(STORE.read_text()) if STORE.exists() else {}


def main(argv):
    items = load()
    if argv[:1] == ["list"]:
        for name, quantity in items.items():
            print(name, quantity)


if __name__ == "__main__":
    main(sys.argv[1:])
