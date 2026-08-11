---
name: codex-delegate
description: Run Codex CLI as a headless delegate. Use when the user names Codex CLI, says "ask Codex", wants `codex exec`, wants a Codex second opinion, or compares coding agents. Do NOT use for interactive sessions, other CLIs, or tasks not meant for delegation.
---

# Codex Delegate

Run Codex as a bounded headless subprocess (`codex exec`) and hand its final response back to the user. Keep the current project as the working directory unless the user specifies another directory.

## Anti-Rationalization

Trigger this skill when the user explicitly asks for Codex CLI, `codex exec`, a Codex second opinion, or a comparison that needs Codex evidence. Do not skip it just because the current agent is already Codex; the requested value is a separate bounded CLI run with captured output.

Pause instead when Codex is missing or unauthenticated, the user wants an interactive session, the task requires exposing secrets, or the requested sandbox/approval level exceeds the user's authorization.

## Runtime Pre-Flight

Read [runtime-setup.md](references/runtime-setup.md) before invoking the wrapper. Verify Python 3.10+ and `codex` or `CODEX_BIN`; stop and report the missing prerequisite instead of inventing an installer or assuming a specific shell.

## Workflow

1. Clarify the delegated objective, scope, and whether Codex may edit files or run commands. Do not delegate secrets or expose protected files in the prompt.
2. Resolve the project directory to an absolute path. Prefer the current working directory. Verify it exists before starting.
3. Run the bundled wrapper with the Python command discovered by [runtime-setup.md](references/runtime-setup.md).
4. Read [headless-reference.md](references/headless-reference.md) when flags, sandboxing, sessions, output parsing, or authentication details are needed.

5. Report the wrapper's result, output-file path, exit status, and any stderr warning. A successful process is not proof that the requested change is correct: inspect the diff and run relevant tests independently when the delegated task changed files.
6. If the task is long-running, use a generous explicit timeout. Never create a hidden daemon, polling loop, or unbounded background process.

## Wrapper behavior

- `delegate_codex.py` invokes `codex` directly, never through a shell, and supports `CODEX_BIN` for an explicit executable path.
- It uses Codex headless mode with `codex exec`, `--cd`, `--json` (JSONL events), `--skip-git-repo-check`, and `--output-last-message <file>` to capture the final agent message cleanly. Because `--json` emits a JSONL event stream, the wrapper reads the final response from the output-message file rather than parsing the whole stream as one object.
- It runs in the read-only sandbox by default. It adds `--sandbox workspace-write --approve-for-me` only when `--always-approve` is requested, and the fully unsandboxed `--dangerously-bypass-approvals-and-sandbox` only when `--full-access` is requested.
- It writes the JSONL event stream, stderr, the final-message file, and a small result manifest to a temporary output directory, then prints the manifest as JSON with the final response under `response`.
- It returns nonzero for missing Codex, an invalid project directory, timeout, or a failed process. Do not hide these failures.
- Prefer a one-shot invocation. Use `--resume` only when the user explicitly asks for a resumable Codex session.

## Safety and verification

- Do not read or print `OPENAI_API_KEY`, ChatGPT/OAuth tokens, `~/.codex/auth.json`, `.env*`, private keys, or browser profiles.
- Do not add MCP servers, disable repository protections, publish code, push commits, or delete data unless the user explicitly asks for that exact action.
- Default to the read-only sandbox. Only escalate to `--always-approve` (workspace-write) or `--full-access` when the user authorizes autonomous edits and the directory is trusted.
- Treat Codex's report as unverified. Inspect changed files, `git diff`, and tests from the controlling agent.
- If `codex` is not found, tell the user to verify the official installation and PATH; do not install packages or run an installer automatically.

## Resources

Use `references/runtime-setup.md` for Python and CLI pre-flight, `scripts/delegate_codex.py` for deterministic invocation, and `references/headless-reference.md` for the documented Codex interface.
