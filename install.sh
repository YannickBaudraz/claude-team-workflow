#!/usr/bin/env bash
# Install the team workflow for Claude Code on this machine.
#   1. Link this repo's skills into ~/.claude/skills.
#   2. Install the community skills listed in install/community-skills.txt, each at its pinned commit.
#   3. Copy the merge guard to ~/.claude/hooks/, then merge install/settings-fragment.json into
#      ~/.claude/settings.json, after showing the diff.
#   4. Install Matt Pocock's plugin at the commit the fragment pins.
#   5. Check the registry against the result.
# Safe to re-run. Needs: claude, npx (skills CLI), jq, python3.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"
SETTINGS="$HOME/.claude/settings.json"

for tool in claude npx jq python3; do
  command -v "$tool" >/dev/null || { echo "Missing tool: $tool"; exit 1; }
done

echo "== 1. Linking this repo's skills"
mkdir -p "$SKILLS_DIR"
for skill_path in "$REPO"/skills/*/; do
  name="$(basename "$skill_path")"
  target="$SKILLS_DIR/$name"
  if [ -L "$target" ]; then
    ln -sfn "${skill_path%/}" "$target"
  elif [ -e "$target" ]; then
    echo "  $target exists and is not a link; move it away, then re-run."
    exit 1
  else
    ln -s "${skill_path%/}" "$target"
  fi
  echo "  $name -> ${skill_path%/}"
done

echo "== 2. Installing community skills"
grep -v -E '^\s*(#|$)' "$REPO/install/community-skills.txt" | while read -r source skills; do
  args=()
  for skill in $skills; do args+=(-s "$skill"); done
  (cd /tmp && npx --yes skills@1.7.2 add "$source" -g -y -a claude-code "${args[@]}" >/dev/null </dev/null)
  echo "  $source: $skills"
done

echo "== 3. Merging the settings fragment"
# The guard goes in before its settings entry. The copy never moves with a branch checkout of this
# repo; when it is missing, the machine-wide entry lets calls through (each project keeps its own copy).
mkdir -p "$HOME/.claude/hooks"
install -m 0755 "$REPO/skills/ask-team/hooks/merge-guard.py" "$HOME/.claude/hooks/merge-guard.py"
echo "  merge guard copied to ~/.claude/hooks/merge-guard.py"
[ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"
merged="$(mktemp)"
jq -s '.[0] as $current | .[1] as $fragment
  | ($current * $fragment)
  | .permissions.deny = (($current.permissions.deny // []) + (($fragment.permissions.deny // []) - ($current.permissions.deny // [])))
  | .extraKnownMarketplaces = (($current.extraKnownMarketplaces // {}) + ($fragment.extraKnownMarketplaces // {}))
  | ([($fragment.hooks.PreToolUse // [])[].hooks[].command]) as $ours
  | .hooks.PreToolUse = ([($current.hooks.PreToolUse // [])[]
        | .hooks = [(.hooks // [])[] | select((.command // "") | test("merge-guard\\.py") | not)]
        | select(.hooks | length > 0)]
      + ($fragment.hooks.PreToolUse // []))' \
  "$SETTINGS" "$REPO/install/settings-fragment.json" > "$merged"
if diff -u <(jq -S . "$SETTINGS") <(jq -S . "$merged"); then
  echo "  settings already up to date"
else
  read -r -p "  Apply these changes to $SETTINGS? [y/N] " answer || answer=""
  if [ "$answer" = "y" ]; then
    cp "$SETTINGS" "$SETTINGS.bak-$(date +%Y%m%d-%H%M%S)"
    cp "$merged" "$SETTINGS"
    echo "  applied (previous file kept as a .bak)"
  else
    echo "  skipped"
  fi
fi
rm -f "$merged"

echo "== 4. Installing Matt Pocock's plugin at its pinned commit"
# The fragment declares his marketplace with the plugin pinned to a commit. Claude Code registers a
# marketplace declared in settings when a session starts, so a first install needs one session in between.
INSTALLED="$HOME/.claude/plugins/installed_plugins.json"
MARKETPLACES="$HOME/.claude/plugins/known_marketplaces.json"
pinned="$(jq -r '.extraKnownMarketplaces.mattpocock.source.plugins[0].source.sha' "$REPO/install/settings-fragment.json")"
installed="$( [ -f "$INSTALLED" ] && jq -r '.plugins["mattpocock-skills@mattpocock"][0].gitCommitSha // empty' "$INSTALLED" || true)"
if [ "$installed" = "$pinned" ]; then
  echo "  mattpocock-skills@mattpocock already at ${pinned:0:7}"
elif [ -f "$MARKETPLACES" ] && jq -e --arg sha "$pinned" \
    '.mattpocock.source.source == "settings" and .mattpocock.source.plugins[0].source.sha == $sha' "$MARKETPLACES" >/dev/null; then
  [ -n "$installed" ] && claude plugin uninstall mattpocock-skills@mattpocock >/dev/null </dev/null
  claude plugin install mattpocock-skills@mattpocock >/dev/null </dev/null
  now="$(jq -r '.plugins["mattpocock-skills@mattpocock"][0].gitCommitSha // "nothing"' "$INSTALLED")"
  echo "  mattpocock-skills@mattpocock installed at ${now:0:7}"
else
  # Also after a pin upgrade: until a session registers the new pin, an install would take the old one.
  echo "  Claude Code has not registered this pin yet: start a Claude Code session once, then re-run install.sh"
fi
claude plugin disable mattpocock-skills@claude-plugins-official >/dev/null 2>&1 </dev/null || true

echo "== 5. Checking the registry"
python3 "$SKILLS_DIR/ask-team/scripts/check-registry.py"
