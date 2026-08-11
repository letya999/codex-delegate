# Codex headless reference

This skill follows OpenAI's Codex CLI (verified against `codex-cli` 0.147.x on 2026-08-11):

- Headless invocation: `codex exec "..."` (alias `codex e`); prompt may also come from stdin
- Working directory: `--cd <DIR>` / `-C <DIR>`; extra writable roots via `--add-dir <DIR>`
- Machine-readable output: `--json` (a JSONL event stream, one event per line)
- Final message only: `--output-last-message <FILE>` / `-o <FILE>` writes the agent's last message to a file
- Model selection: `--model <MODEL>` / `-m <MODEL>`
- Sandbox policy: `--sandbox read-only | workspace-write | danger-full-access` (`-s`)
- Auto-approval within a sandbox: `--approve-for-me` (routes approvals through automatic review, workspace-write)
- Full autonomy (no sandbox, no approvals): `--dangerously-bypass-approvals-and-sandbox` (EXTREMELY DANGEROUS)
- Run outside a git repo: `--skip-git-repo-check`
- Do not persist a session: `--ephemeral`
- Resumable sessions: `codex exec resume <ID>` or `codex exec resume --last`

Authentication is expected to be preconfigured by the user through `codex login` (ChatGPT/OAuth) or `OPENAI_API_KEY`. Never inspect or print credentials. If authentication fails, return Codex's error and ask the user to authenticate separately.

Notes:

- Because `--json` emits a JSONL event stream (not a single object), parse the final answer from the `--output-last-message` file, not by `json.loads()` on the whole stdout. The wrapper does exactly this and surfaces the file's contents as `response`.
- The wrapper defaults to the read-only sandbox. `--always-approve` maps to `--sandbox workspace-write --approve-for-me`; `--full-access` maps to `--dangerously-bypass-approvals-and-sandbox`.
- `codex exec` normally requires a git repository; the wrapper always passes `--skip-git-repo-check` so non-git directories still work.

Primary sources:

- [Codex CLI reference](https://developers.openai.com/codex/cli/)
- [Codex non-interactive / exec usage](https://github.com/openai/codex)
- Local help: `codex exec --help`
