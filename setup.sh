#!/bin/bash
#
# swiss-website-design skill setup
#
# Installs this skill under:
#   ${CODEX_HOME:-$HOME/.codex}/skills/swiss-website-design

set -euo pipefail

SKILL_NAME="swiss-website-design"
CODEX_ROOT="${CODEX_HOME:-$HOME/.codex}"
SKILL_DIR="$CODEX_ROOT/skills/$SKILL_NAME"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Swiss Website Design Skill Setup ==="
echo

if [ ! -f "$SCRIPT_DIR/SKILL.md" ]; then
    echo "Could not find SKILL.md at $SCRIPT_DIR/SKILL.md"
    exit 1
fi

if [ -d "$SKILL_DIR" ] || [ -L "$SKILL_DIR" ]; then
    echo "Found existing skill at $SKILL_DIR"
    read -r -p "Overwrite? (y/N) " -n 1 REPLY
    echo
    if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    rm -rf -- "$SKILL_DIR"
fi

mkdir -p "$SKILL_DIR"

echo "Installing skill files..."
for item in SKILL.md agents references; do
    if [ -e "$SCRIPT_DIR/$item" ]; then
        cp -R "$SCRIPT_DIR/$item" "$SKILL_DIR/$item"
    fi
done

echo
echo "Installed to $SKILL_DIR"
echo
echo 'To use: open Codex in a website project and mention $swiss-website-design'
echo "Restart Codex if the installed skill does not appear in the current session."
