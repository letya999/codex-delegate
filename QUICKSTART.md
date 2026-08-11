# Codex Delegate Quickstart

Use this skill when the caller explicitly wants Codex CLI to run as a separate headless agent.

## Requirements

- Python 3.10+
- Codex CLI on `PATH`, or `CODEX_BIN` set to the executable path
- Codex authentication already configured by the user

## Run

POSIX shell on macOS, Linux, or WSL:

```sh
python3 scripts/delegate_codex.py \
  --cwd "$PWD" \
  --task "Review this repository and report the highest-risk issue." \
  --timeout 45m
```

Windows PowerShell:

```powershell
py -3 .\scripts\delegate_codex.py `
  --cwd (Get-Location).Path `
  --task "Review this repository and report the highest-risk issue." `
  --timeout 45m
```

If `python3` or `py -3` is not available, use the Python command discovered in `references/runtime-setup.md`.

## Result

The wrapper prints a JSON manifest with `response`, `exit_code`, `events`, `stderr`, and `output_dir`. Treat Codex's answer as unverified until the controlling agent checks the diff and tests.
