<p align="center">
  <strong>English</strong> · <a href="README.ru.md">Русский</a>
</p>

<p align="center">
  <h1 align="center">Codex Delegate</h1>
</p>

<p align="center">
  <a href="https://github.com/letya999/codex-delegate"><img src="https://img.shields.io/badge/status-active-brightgreen" alt="status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License: MIT"></a>
  <a href="https://skills.sh"><img src="https://img.shields.io/badge/skills.sh-discoverable-black" alt="skills.sh"></a>
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/cli-codex-purple" alt="CLI: codex">
</p>

Headless OpenAI Codex CLI delegate skill by [Artem Letyushev](https://github.com/letya999).

The command is `scripts/delegate_codex.py`. The primary consumer is the controlling agent or orchestrator: every execution runs Codex once as a bounded, non-interactive subprocess (`codex exec`) and returns one structured JSON envelope.

---

## One objective, bounded subprocess, zero trust

The wrapper acts as a deterministic isolation layer between your controlling agent and the Codex CLI:

- **Single non-interactive execution:** Invokes `codex exec` directly via `subprocess.run(..., shell=False)` without terminal takeovers.
- **Read-only sandbox by default:** Enforces read-only sandboxing unless explicit approval or full-access flags are provided.
- **Clean message capture:** Uses `--output-last-message` to extract the final agent response cleanly without noisy JSONL parsing.
- **Zero-trust verification:** Outputs are unverified until independently confirmed by diffs and tests.
- **Credential isolation:** Never inspects or prints `OPENAI_API_KEY`, `~/.codex/auth.json`, or `.env` files.

## Capability matrix

| Capability / Setting | Specification | Behavior & Guarantees |
|---|---|---|
| **Headless command** | `codex exec "<task>"` | Non-interactive execution in execution mode |
| **Workspace scoping** | `--cd <cwd>` | Restricts Codex to the target project working directory |
| **Event stream** | `--json` | Captures JSONL event stream to `events.jsonl` |
| **Response extraction** | `--output-last-message <file>` | Writes clean final agent message directly into manifest |
| **Default sandbox** | Read-only sandbox | Prevents unintentional filesystem mutation by default |
| **Autonomous edits** | `--always-approve` | Enables `--sandbox workspace-write --approve-for-me` |
| **Full bypass** | `--full-access` | Passes `--dangerously-bypass-approvals-and-sandbox` only when explicitly authorized |
| **Executable override** | `CODEX_BIN` env var | Custom executable path before searching PATH |
| **Standard exit codes** | `0, 2, 65, 124, 126, 127` | Predictable error routing for orchestrators |

## Install

With `npx skills`:

```bash
npx skills add letya999/codex-delegate
```

Or clone into an agent skill directory:

```bash
git clone https://github.com/letya999/codex-delegate.git .agents/skills/codex-delegate
```

## Quick Start

### POSIX (macOS, Linux, WSL)

```bash
python3 scripts/delegate_codex.py \
  --cwd "$PWD" \
  --task "Review this repository and report the highest-risk issue." \
  --timeout 45m
```

### Windows PowerShell

```powershell
py -3 .\scripts\delegate_codex.py `
  --cwd (Get-Location).Path `
  --task "Review this repository and report the highest-risk issue." `
  --timeout 45m
```

---

<details>
<summary>JSON Manifest Schema & Agent Integration</summary>

The wrapper writes `events.jsonl`, `stderr.log`, `last-message.txt`, and `result.json` into a temporary directory:

```json
{
  "tool": "codex",
  "cwd": "C:\\work\\repo",
  "exit_code": 0,
  "output_dir": "C:\\Temp\\codex-delegate-xyz",
  "stdout": "C:\\Temp\\codex-delegate-xyz\\events.jsonl",
  "events": "C:\\Temp\\codex-delegate-xyz\\events.jsonl",
  "stderr": "C:\\Temp\\codex-delegate-xyz\\stderr.log",
  "response": "Final agent answer captured from --output-last-message"
}
```

If Codex completes with exit code 0 but no response message can be extracted, the wrapper returns code `65`.

</details>

<details>
<summary>CLI Flags & Configuration Reference</summary>

| Flag | Type | Description |
|---|---|---|
| `--cwd` | Path (required) | Target project directory. Exits with `2` if missing. |
| `--task` | String (required) | Delegated instruction / prompt for Codex. |
| `--timeout` | Duration (default: `45m`) | Timeout formatted as `90s`, `45m`, `2h`, or integer seconds. |
| `--model` | String | Model override passed to Codex. |
| `--always-approve` | Flag | Escalates to `--sandbox workspace-write --approve-for-me`. |
| `--full-access` | Flag | Escalates to `--dangerously-bypass-approvals-and-sandbox`. |
| `--resume` | String | Resumes an existing session ID. |
| `--output-dir` | Path | Custom artifact directory. |

</details>

<details>
<summary>Safety Posture & Credential Guardrails</summary>

- **No credential leaks:** Never reads or logs `OPENAI_API_KEY`, OAuth tokens, or `~/.codex/auth.json`.
- **Read-only by default:** Default read-only sandbox protects the host system.
- **Anti-recursion rule:** Delegated Codex instances must not recursively spawn further delegate wrappers.

</details>

<details>
<summary>Independent Verification Protocol</summary>

Outputs are unverified evidence. After delegated file modifications:

1. Check changes independently: `git diff --stat` and `git diff`.
2. Run test suites outside the delegated environment: `pytest`, `npm test`, etc.
3. Verify newly generated files and imports.

</details>

<details>
<summary>Test Suite & Quality Checks</summary>

Run the test suite with standard library `unittest`:

```bash
python -m unittest discover -s tests -v
```

</details>

<details>
<summary>Agent Skill Entry Points</summary>

- [SKILL.md](SKILL.md) — Skill instruction specification for coding agents.
- [QUICKSTART.md](QUICKSTART.md) — Quick command reference.
- [references/runtime-setup.md](references/runtime-setup.md) — Cross-platform pre-flight checks.
- [references/headless-reference.md](references/headless-reference.md) — Codex CLI headless reference.
- [.well-known/agent-skills/index.json](.well-known/agent-skills/index.json) — Discovery index for skills.sh.
- [dist/codex-delegate.zip](dist/codex-delegate.zip) — Discoverable archive artifact.

</details>

<details>
<summary>License</summary>

MIT License. See [LICENSE](LICENSE) for full text. Copyright (c) 2026 Artem Letyushev.

</details>
