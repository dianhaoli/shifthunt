#!/usr/bin/env bash
# GPT agents (Codex CLI, `codex exec`), as in the paper: JSON event stream, reasoning effort max, no sandbox
# prompts inside the container (the container is the sandbox).
# stdout (events) and stderr are written to /logs by the entrypoint (root): the agent cannot write /logs.
set -uo pipefail
exec codex exec --json --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox \
    -m "$AGENT_MODEL" -c model_reasoning_effort=max - < "$1"
