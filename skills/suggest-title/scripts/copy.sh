#!/bin/sh
# Put "$1" on the clipboard, without a trailing newline so pasting it does not submit it.
# Exits 1 and says so when no clipboard tool is found.
text=$1
if grep -qi microsoft /proc/version 2>/dev/null && command -v clip.exe >/dev/null; then
  printf '%s' "$text" | clip.exe        # WSL: the Windows clipboard the terminal pastes from
elif command -v pbcopy >/dev/null; then
  printf '%s' "$text" | pbcopy
elif [ -n "$WAYLAND_DISPLAY" ] && command -v wl-copy >/dev/null; then
  printf '%s' "$text" | wl-copy
elif command -v xclip >/dev/null; then
  printf '%s' "$text" | xclip -selection clipboard
elif command -v xsel >/dev/null; then
  printf '%s' "$text" | xsel --clipboard --input
else
  echo "no clipboard tool found (clip.exe, pbcopy, wl-copy, xclip or xsel)" >&2
  exit 1
fi
