#!/usr/bin/env python3
"""Run Codex once in headless mode (codex exec) and capture its result."""

from __future__ import annotations

import argparse
import json
import os
import signal
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run_bounded(command: list[str], cwd: Path, timeout: float) -> subprocess.CompletedProcess[str]:
    """Run in a process group so a timeout can terminate the whole CLI tree."""
    group_options = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True})
    process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", **group_options)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        else:
            os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        exc.stdout, exc.stderr = stdout, stderr
        raise
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def parse_duration(value: str) -> float:
    value = value.strip().lower()
    units = {"s": 1, "m": 60, "h": 3600}
    if value[-1:] in units:
        seconds = float(value[:-1]) * units[value[-1]]
    else:
        seconds = float(value)
    if seconds <= 0:
        raise ValueError("timeout must be greater than zero")
    return seconds


def find_codex() -> str | None:
    explicit = os.environ.get("CODEX_BIN")
    if explicit:
        return explicit
    found = shutil.which("codex")
    if found:
        return found
    for candidate in (
        Path.home() / ".codex" / "bin" / "codex.exe",
        Path.home() / ".codex" / "bin" / "codex",
        Path.home() / ".local" / "bin" / "codex.exe",
        Path.home() / ".local" / "bin" / "codex",
    ):
        if candidate.is_file():
            return str(candidate)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", required=True, help="Absolute project directory")
    parser.add_argument("--task", required=True, help="Task to delegate")
    parser.add_argument("--timeout", default="45m", help="Timeout, e.g. 90s, 45m, 2h")
    parser.add_argument("--model", help="Optional Codex model")
    parser.add_argument("--resume", help="Optional session id to resume")
    parser.add_argument("--always-approve", action="store_true", help="Allow workspace-write edits with auto-approval")
    parser.add_argument("--full-access", action="store_true", help="Bypass all approvals and sandbox (DANGEROUS)")
    parser.add_argument("--output-dir", help="Directory for captured output")
    args = parser.parse_args()

    cwd = Path(args.cwd).expanduser().resolve()
    if not cwd.is_dir():
        print(f"error: project directory does not exist: {cwd}", file=sys.stderr)
        return 2

    codex = find_codex()
    if not codex:
        print("error: codex executable not found; set CODEX_BIN or add codex to PATH", file=sys.stderr)
        return 127
    if not Path(codex).is_file():
        resolved = shutil.which(codex)
        if not resolved:
            print("error: codex executable not found; set CODEX_BIN or add codex to PATH", file=sys.stderr)
            return 127
        codex = resolved

    try:
        timeout = parse_duration(args.timeout)
    except (TypeError, ValueError) as exc:
        parser.error(f"invalid --timeout: {exc}")

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else Path(tempfile.mkdtemp(prefix="codex-delegate-"))
    output_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = output_dir / "events.jsonl"
    stderr_path = output_dir / "stderr.log"
    last_message_path = output_dir / "last-message.txt"
    manifest_path = output_dir / "result.json"

    command = [codex, "exec", "--cd", str(cwd), "--json", "--skip-git-repo-check", "--output-last-message", str(last_message_path)]
    if args.model:
        command.extend(["--model", args.model])
    if args.full_access:
        command.append("--dangerously-bypass-approvals-and-sandbox")
    elif args.always_approve:
        command.extend(["--sandbox", "workspace-write", "--approve-for-me"])
    if args.resume:
        # codex exec resume <ID> ...; prompt is passed after the id.
        command = [codex, "exec", "resume", args.resume, "--cd", str(cwd), "--json", "--skip-git-repo-check", "--output-last-message", str(last_message_path)]
        if args.model:
            command.extend(["--model", args.model])
        if args.full_access:
            command.append("--dangerously-bypass-approvals-and-sandbox")
        elif args.always_approve:
            command.extend(["--sandbox", "workspace-write", "--approve-for-me"])
    command.append(args.task)

    try:
        completed = run_bounded(command, cwd, timeout)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        stdout_path.write_text(stdout if isinstance(stdout, str) else stdout.decode("utf-8", "replace"), encoding="utf-8")
        stderr_path.write_text(stderr if isinstance(stderr, str) else stderr.decode("utf-8", "replace"), encoding="utf-8")
        manifest = {"tool": "codex", "cwd": str(cwd), "exit_code": 124, "timed_out": True, "output_dir": str(output_dir), "stdout": str(stdout_path), "events": str(stdout_path), "stderr": str(stderr_path)}
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        print(f"error: Codex timed out after {args.timeout}; output: {output_dir}", file=sys.stderr)
        return 124
    except OSError as exc:
        print(f"error: could not start Codex: {exc}", file=sys.stderr)
        return 126

    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")

    manifest = {"tool": "codex", "cwd": str(cwd), "exit_code": completed.returncode, "output_dir": str(output_dir), "stdout": str(stdout_path), "events": str(stdout_path), "stderr": str(stderr_path)}
    if last_message_path.is_file():
        manifest["response"] = last_message_path.read_text(encoding="utf-8", errors="replace").strip()
        manifest["last_message"] = str(last_message_path)
    else:
        manifest["parse_error"] = "Codex did not write a final message file"

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))

    if completed.returncode == 0 and "response" not in manifest:
        print(f"error: Codex produced no final message; events: {stdout_path}", file=sys.stderr)
        return 65
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
