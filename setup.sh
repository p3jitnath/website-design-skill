#!/bin/bash
#
# swiss-website-design skill setup
#
# Usage: ./setup.sh [--harness codex|claude]
# Default harness: codex

set -euo pipefail

SKILL_NAME="swiss-website-design"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HARNESS="codex"

usage() {
    echo "Usage: $0 [--harness codex|claude]"
    echo
    echo "Install the $SKILL_NAME skill for Codex (default) or Claude Code."
    echo "  codex   ${CODEX_HOME:-$HOME/.codex}/skills/$SKILL_NAME"
    echo "  claude  ${CLAUDE_HOME:-$HOME/.claude}/skills/$SKILL_NAME"
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --harness)
            [ "$#" -ge 2 ] || { echo "Missing value for --harness" >&2; usage >&2; exit 2; }
            HARNESS="$2"
            shift 2
            ;;
        --harness=*) HARNESS="${1#*=}"; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
done

case "$HARNESS" in
    codex) HARNESS_NAME="Codex"; HARNESS_ROOT="${CODEX_HOME:-$HOME/.codex}"; INVOCATION="\$$SKILL_NAME" ;;
    claude) HARNESS_NAME="Claude Code"; HARNESS_ROOT="${CLAUDE_HOME:-$HOME/.claude}"; INVOCATION="/$SKILL_NAME" ;;
    *) echo "Unsupported harness: $HARNESS (expected codex or claude)" >&2; exit 2 ;;
esac

SKILL_DIR="$HARNESS_ROOT/skills/$SKILL_NAME"

echo "=== Swiss Website Design Skill Installer ==="
echo "Harness: $HARNESS_NAME"
echo "Destination: $SKILL_DIR"
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

echo "Installing $SKILL_NAME for $HARNESS_NAME..."
for item in SKILL.md references; do
    if [ -e "$SCRIPT_DIR/$item" ]; then
        cp -R "$SCRIPT_DIR/$item" "$SKILL_DIR/$item"
    fi
done

if [ "$HARNESS" = "codex" ] && [ -e "$SCRIPT_DIR/agents" ]; then
    cp -R "$SCRIPT_DIR/agents" "$SKILL_DIR/agents"
fi

echo
echo "Installation complete."
echo "Skill: $SKILL_NAME"
echo "Harness: $HARNESS_NAME"
echo "Location: $SKILL_DIR"
echo "Invoke: $INVOCATION"
echo "Restart $HARNESS_NAME if the installed skill does not appear in the current session."
