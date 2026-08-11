# Codex Delegate

Headless Codex CLI delegate skill by [Artem Letyushev](https://github.com/letya999).

This repository packages a cross-platform agent skill that lets a controlling agent run `codex exec` once, non-interactively, capture the final message and event stream, and verify the work outside the delegated agent.

## What It Does

- Runs `codex exec` through `scripts/delegate_codex.py`
- Captures JSONL events, stderr, exit code, output files, and the final response
- Supports macOS, Linux, WSL, and Windows
- Uses `CODEX_BIN` when the executable is not on `PATH`
- Defaults to Codex read-only sandboxing
- Keeps delegated output untrusted until the controlling agent checks diffs and tests

## Install

With `npx skills`:

```sh
npx skills add letya999/codex-delegate
```

Or copy this repository into an agent skill directory such as `.agents/skills/`, `.claude/skills/`, or `~/.codex/skills/`.

## Quick Start

```sh
python3 scripts/delegate_codex.py \
  --cwd "$PWD" \
  --task "Review this repository and report the highest-risk issue." \
  --timeout 45m
```

Windows users can run the same wrapper with `py -3`. See [QUICKSTART.md](QUICKSTART.md) and [references/runtime-setup.md](references/runtime-setup.md) for the full cross-platform pre-flight.

## Agent Skill Entry Points

- [SKILL.md](SKILL.md) is the skill instruction file.
- [.well-known/agent-skills/index.json](.well-known/agent-skills/index.json) is the discovery index.
- [dist/codex-delegate.zip](dist/codex-delegate.zip) is the archive artifact referenced by the index.

## License

MIT License. See [LICENSE](LICENSE).
