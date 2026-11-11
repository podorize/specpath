"""Run the 90 Gold cases as independent, read-only agentic reviews.

The model starts from the same label-free columns supplied to human reviewers.
It can inspect any file at the exact anchor commit, search the snapshot, inspect
pre-anchor path history, and use GitHub web search for scope discovery. All tool
calls and returned evidence are recorded per case.
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "interim" / "validation_final_90_en.csv"
PROMPT_FILE = ROOT / "validation" / "LLM_JUDGE_PROMPT_FINAL_90_OPENAI_AGENTIC.md"
PROTOCOL_FILE = ROOT / "validation" / "OPENAI_SOL_90_AGENTIC_PROTOCOL.md"
SCHEMA_FILE = ROOT / "validation" / "llm_judge_output_schema_openai_agentic.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "openai_sol_90_agentic"
GIT_CACHE = ROOT / "outputs" / "openai_sol_90_v3" / "git_cache"
ENV_FILE = ROOT / ".env.local"
MODEL = "gpt-6.1-sol"
API_URL = "https://api.openai.com/v1/responses"
MAX_TOOL_CALLS = 50
MAX_ROUNDS = 20
MAX_TOOL_TEXT = 30_000

LABEL_COLUMNS = {
    "reviewer_id",
    "manual_classification",
    "evidence_note",
    "access_issue",
    "r1_initial_classification",
    "r2_initial_classification",
    "gold_human_classification",
    "adjudication_rationale",
    "gemini_classification",
    "classification",
    "exists_at_anchor",
}

CLASSES = {
    "confirmed_exists",
    "confirmed_missing_problematic",
    "expected_absence_create",
    "expected_absence_move_or_delete",
    "external_repository_reference",
    "non_file_reference",
    "ambiguous_reference",
    "inaccessible_or_invalid",
}

WRITE_LOCK = threading.Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if key:
        return key
    if ENV_FILE.exists():
        for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if raw.startswith("OPENAI_API_KEY="):
                key = raw.split("=", 1)[1].strip().strip('"').strip("'")
                if key:
                    return key
    raise RuntimeError("No usable OPENAI_API_KEY in the environment or .env.local")


def load_cases() -> list[dict[str, Any]]:
    with SOURCE.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 90 or [row["review_id"] for row in rows] != [f"F{i:03d}" for i in range(1, 91)]:
        raise ValueError("Expected ordered F001-F090 source rows")
    for row in rows:
        leaked = LABEL_COLUMNS.intersection(row)
        leaked -= {"reviewer_id", "manual_classification", "evidence_note", "access_issue"}
        if leaked:
            raise ValueError(f"Unexpected prohibited source columns: {sorted(leaked)}")
    allowed = [
        "review_id",
        "repo_name",
        "anchor_sha",
        "artifact_path",
        "code_path",
        "resolved_path",
        "task_url",
        "literal_path_url",
        "anchor_path",
        "anchor_path_url",
        "task_context",
    ]
    return [{key: row.get(key, "") for key in allowed} for row in rows]


def normalize_path(path: str) -> str:
    value = path.replace("\\", "/").strip()
    while value.startswith("./"):
        value = value[2:]
    if not value or value.startswith("/") or "\x00" in value or ".." in PurePosixPath(value).parts:
        raise ValueError("Path must be a relative repository path without '..'")
    return value


def run_git(repo_dir: Path, args: list[str], *, timeout: int = 120, binary: bool = False) -> subprocess.CompletedProcess[Any]:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    return subprocess.run(
        ["git", "--git-dir", str(repo_dir), *args],
        capture_output=True,
        text=not binary,
        timeout=timeout,
        check=False,
        env=env,
    )


class RepositoryTools:
    def __init__(self, case: dict[str, Any]):
        self.case = case
        self.review_id = case["review_id"]
        self.repo_dir = GIT_CACHE / self.review_id
        self.anchor = case["anchor_sha"]
        self.repo_name = case["repo_name"]
        self.anchor_available = False
        self.access_error = ""
        if not (self.repo_dir / "HEAD").exists():
            self.tree = []
            self.tree_set = set()
            self.access_error = "frozen_git_cache_missing"
            return
        check = run_git(self.repo_dir, ["cat-file", "-e", f"{self.anchor}^{{commit}}"], timeout=30)
        if check.returncode != 0:
            self.tree = []
            self.tree_set = set()
            self.access_error = "anchor_commit_unavailable_in_frozen_cache"
            return
        tree_result = run_git(self.repo_dir, ["ls-tree", "-r", "--name-only", self.anchor], timeout=120)
        if tree_result.returncode != 0:
            self.tree = []
            self.tree_set = set()
            self.access_error = "anchor_tree_unreadable"
            return
        self.tree = [line for line in tree_result.stdout.splitlines() if line]
        self.tree_set = set(self.tree)
        self.anchor_available = True

    def unavailable(self, operation: str) -> dict[str, Any]:
        return {
            "repository": self.repo_name,
            "anchor_sha": self.anchor,
            "operation": operation,
            "status": "anchor_unavailable",
            "error": self.access_error,
        }

    def list_tree(self, prefix: str, max_results: int) -> dict[str, Any]:
        if not self.anchor_available:
            return self.unavailable("list_tree")
        clean = prefix.replace("\\", "/").strip().lstrip("./")
        if ".." in PurePosixPath(clean or ".").parts:
            raise ValueError("Invalid prefix")
        limit = max(1, min(int(max_results), 500))
        matches = [path for path in self.tree if not clean or path.startswith(clean)]
        return {
            "repository": self.repo_name,
            "anchor_sha": self.anchor,
            "prefix": clean,
            "total_matches": len(matches),
            "paths": matches[:limit],
            "truncated": len(matches) > limit,
        }

    def search_paths(self, query: str, max_results: int) -> dict[str, Any]:
        if not self.anchor_available:
            return self.unavailable("search_paths")
        needle = query.strip()
        if not needle:
            raise ValueError("Search query cannot be empty")
        limit = max(1, min(int(max_results), 200))
        if any(char in needle for char in "*?[]"):
            matches = [path for path in self.tree if fnmatch.fnmatch(path.lower(), needle.lower())]
            mode = "glob"
        else:
            lowered = needle.lower()
            matches = [path for path in self.tree if lowered in path.lower()]
            mode = "case_insensitive_substring"
        return {
            "repository": self.repo_name,
            "anchor_sha": self.anchor,
            "query": needle,
            "mode": mode,
            "total_matches": len(matches),
            "paths": matches[:limit],
            "truncated": len(matches) > limit,
        }

    def read_file(self, path: str, start_line: int, end_line: int) -> dict[str, Any]:
        if not self.anchor_available:
            return self.unavailable("read_file")
        clean = normalize_path(path)
        if clean not in self.tree_set:
            return {
                "repository": self.repo_name,
                "anchor_sha": self.anchor,
                "path": clean,
                "status": "not_found_at_anchor",
            }
        start = max(1, int(start_line))
        end = max(start, min(int(end_line), start + 399))
        result = run_git(self.repo_dir, ["show", f"{self.anchor}:{clean}"], timeout=120, binary=True)
        if result.returncode != 0:
            return {
                "repository": self.repo_name,
                "anchor_sha": self.anchor,
                "path": clean,
                "status": "read_failed",
                "error": result.stderr.decode("utf-8", errors="replace")[-1000:],
            }
        payload: bytes = result.stdout
        if b"\x00" in payload[:8192]:
            return {
                "repository": self.repo_name,
                "anchor_sha": self.anchor,
                "path": clean,
                "status": "binary_file",
                "byte_size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        text = payload.decode("utf-8", errors="replace")
        lines = text.splitlines()
        selected = lines[start - 1 : end]
        numbered = "\n".join(f"{index}: {value}" for index, value in enumerate(selected, start=start))
        return {
            "repository": self.repo_name,
            "anchor_sha": self.anchor,
            "path": clean,
            "status": "found",
            "total_lines": len(lines),
            "returned_lines": [start, min(end, len(lines))],
            "content": numbered[:MAX_TOOL_TEXT],
            "content_truncated": len(numbered) > MAX_TOOL_TEXT,
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    def search_content(self, query: str, path_prefix: str, max_results: int) -> dict[str, Any]:
        if not self.anchor_available:
            return self.unavailable("search_content")
        needle = query.strip()
        if not needle:
            raise ValueError("Search query cannot be empty")
        prefix = path_prefix.replace("\\", "/").strip().lstrip("./")
        if ".." in PurePosixPath(prefix or ".").parts:
            raise ValueError("Invalid path prefix")
        limit = max(1, min(int(max_results), 100))
        args = ["grep", "-n", "-I", "-F", "-e", needle, self.anchor, "--"]
        if prefix:
            args.append(f"{prefix}*")
        try:
            result = run_git(self.repo_dir, args, timeout=180)
        except subprocess.TimeoutExpired:
            return {
                "repository": self.repo_name,
                "anchor_sha": self.anchor,
                "query": needle,
                "path_prefix": prefix,
                "status": "timed_out",
                "matches": [],
            }
        raw_lines = result.stdout.splitlines()
        matches = []
        for raw in raw_lines[:limit]:
            match = re.match(r"^[^:]*:([^:]+):(\d+):(.*)$", raw)
            if match:
                matches.append({"path": match.group(1), "line": int(match.group(2)), "text": match.group(3)[:500]})
            else:
                matches.append({"raw": raw[:700]})
        return {
            "repository": self.repo_name,
            "anchor_sha": self.anchor,
            "query": needle,
            "path_prefix": prefix,
            "status": "completed" if result.returncode in {0, 1} else "search_failed",
            "total_returned_by_git": len(raw_lines),
            "matches": matches,
            "truncated": len(raw_lines) > limit,
            "error": result.stderr[-1000:] if result.returncode not in {0, 1} else "",
        }

    def path_history(self, path: str, max_commits: int) -> dict[str, Any]:
        if not self.anchor_available:
            return self.unavailable("path_history")
        clean = normalize_path(path)
        limit = max(1, min(int(max_commits), 30))
        shallow = run_git(self.repo_dir, ["rev-parse", "--is-shallow-repository"], timeout=30)
        fetch_status = "not_needed"
        if shallow.returncode == 0 and shallow.stdout.strip() == "true":
            url = f"https://github.com/{self.repo_name}.git"
            try:
                fetched = run_git(
                    self.repo_dir,
                    ["fetch", "--deepen=100", "--filter=blob:none", url, self.anchor],
                    timeout=240,
                )
                fetch_status = "deepened" if fetched.returncode == 0 else "deepen_failed"
            except subprocess.TimeoutExpired:
                fetch_status = "deepen_timed_out"
        result = run_git(
            self.repo_dir,
            [
                "log",
                f"-{limit}",
                "--follow",
                "--date=iso-strict",
                "--format=%H%x09%ad%x09%s",
                self.anchor,
                "--",
                clean,
            ],
            timeout=120,
        )
        commits = []
        for line in result.stdout.splitlines():
            parts = line.split("\t", 2)
            if len(parts) == 3:
                commits.append({"sha": parts[0], "date": parts[1], "subject": parts[2]})
        return {
            "repository": self.repo_name,
            "anchor_sha": self.anchor,
            "path": clean,
            "history_scope": "anchor_and_ancestors_only",
            "history_fetch": fetch_status,
            "commits": commits,
            "status": "completed" if result.returncode == 0 else "history_failed",
            "error": result.stderr[-1000:] if result.returncode != 0 else "",
        }

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "list_tree":
            return self.list_tree(arguments["prefix"], arguments["max_results"])
        if name == "search_paths":
            return self.search_paths(arguments["query"], arguments["max_results"])
        if name == "read_file":
            return self.read_file(arguments["path"], arguments["start_line"], arguments["end_line"])
        if name == "search_content":
            return self.search_content(arguments["query"], arguments["path_prefix"], arguments["max_results"])
        if name == "path_history":
            return self.path_history(arguments["path"], arguments["max_commits"])
        raise ValueError(f"Unknown tool: {name}")


def function_tool(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": properties,
            "required": required,
        },
        "strict": True,
    }


def tool_definitions(enable_web: bool) -> list[dict[str, Any]]:
    tools = [
        function_tool(
            "list_tree",
            "List paths from the complete repository tree at this case's exact anchor commit.",
            {"prefix": {"type": "string"}, "max_results": {"type": "integer", "minimum": 1, "maximum": 500}},
            ["prefix", "max_results"],
        ),
        function_tool(
            "search_paths",
            "Search all paths at the anchor by case-insensitive substring or glob.",
            {"query": {"type": "string"}, "max_results": {"type": "integer", "minimum": 1, "maximum": 200}},
            ["query", "max_results"],
        ),
        function_tool(
            "read_file",
            "Open any text file at the exact anchor commit. Use additional calls for more line ranges.",
            {
                "path": {"type": "string"},
                "start_line": {"type": "integer", "minimum": 1},
                "end_line": {"type": "integer", "minimum": 1},
            },
            ["path", "start_line", "end_line"],
        ),
        function_tool(
            "search_content",
            "Search literal text across all text files at the exact anchor commit, optionally under a path prefix.",
            {
                "query": {"type": "string"},
                "path_prefix": {"type": "string"},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 100},
            },
            ["query", "path_prefix", "max_results"],
        ),
        function_tool(
            "path_history",
            "Inspect commits affecting a path at the anchor or its ancestors; never includes commits after the anchor.",
            {"path": {"type": "string"}, "max_commits": {"type": "integer", "minimum": 1, "maximum": 30}},
            ["path", "max_commits"],
        ),
    ]
    if enable_web:
        tools.append(
            {
                "type": "web_search",
                "external_web_access": True,
                "filters": {"allowed_domains": ["github.com", "raw.githubusercontent.com"]},
            }
        )
    return tools


def api_request(api_key: str, payload: dict[str, Any], *, attempts: int = 6) -> dict[str, Any]:
    body = canonical(payload).encode("utf-8")
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            API_URL,
            data=body,
            method="POST",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:4000]
            if error.code not in {408, 409, 429, 500, 502, 503, 504} or attempt == attempts:
                raise RuntimeError(f"OpenAI API HTTP {error.code}: {detail}") from error
        except (urllib.error.URLError, TimeoutError) as error:
            if attempt == attempts:
                raise RuntimeError(f"OpenAI API network failure: {error}") from error
        time.sleep(min(2 ** attempt, 30))
    raise AssertionError("unreachable")


def trace_append(path: Path, event: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical(event) + "\n")


def response_text(response: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                parts.append(content.get("text", ""))
    return "".join(parts).strip()


def validate_prediction(value: dict[str, Any], review_id: str) -> dict[str, Any]:
    if value.get("review_id") != review_id:
        raise ValueError(f"Review id mismatch: expected {review_id}, got {value.get('review_id')}")
    if value.get("classification") not in CLASSES:
        raise ValueError(f"Invalid classification for {review_id}")
    expected_decision = "abstain" if value["classification"] in {"ambiguous_reference", "inaccessible_or_invalid"} else "classify"
    if value.get("decision") != expected_decision:
        raise ValueError(f"Decision/class mismatch for {review_id}")
    return value


def run_case(
    case: dict[str, Any],
    api_key: str,
    prompt: str,
    schema: dict[str, Any],
    output_dir: Path,
    enable_web: bool,
) -> dict[str, Any]:
    review_id = case["review_id"]
    trace_file = output_dir / "traces" / f"{review_id}.jsonl"
    if trace_file.exists():
        trace_file.unlink()
    repo = RepositoryTools(case)
    tools = tool_definitions(enable_web)
    initial = {
        key: value
        for key, value in case.items()
        if key not in LABEL_COLUMNS
    }
    conversation: list[dict[str, Any]] = [
        {"role": "developer", "content": [{"type": "input_text", "text": prompt}]},
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Review this case independently. Begin by opening the task artifact at the anchor commit.\n" + canonical(initial),
                }
            ],
        },
    ]
    usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    tool_count = 0
    tool_names: list[str] = []
    trace_append(trace_file, {"event": "case_start", "at": utc_now(), "case": initial})

    for round_index in range(1, MAX_ROUNDS + 1):
        payload = {
            "model": MODEL,
            "reasoning": {"effort": "low", "mode": "standard"},
            "input": conversation,
            "tools": tools,
            "tool_choice": "auto",
            "parallel_tool_calls": True,
            "max_tool_calls": 40,
            "text": {
                "verbosity": "low",
                "format": {
                    "type": "json_schema",
                    "name": "specpath_agentic_classification",
                    "strict": True,
                    "schema": schema,
                },
            },
            "max_output_tokens": 3000,
            "store": False,
        }
        response = api_request(api_key, payload)
        response_usage = response.get("usage") or {}
        for key in usage:
            usage[key] += int(response_usage.get(key, 0) or 0)
        trace_append(
            trace_file,
            {
                "event": "model_response",
                "at": utc_now(),
                "round": round_index,
                "response_id": response.get("id"),
                "status": response.get("status"),
                "usage": response_usage,
                "output": response.get("output", []),
            },
        )
        output_items = response.get("output", [])
        for item in output_items:
            if item.get("type") == "web_search_call":
                tool_count += 1
                tool_names.append("web_search")
        function_calls = [item for item in output_items if item.get("type") == "function_call"]
        if not function_calls:
            final_text = response_text(response)
            if not final_text:
                raise RuntimeError(f"{review_id} ended without a final message")
            prediction = validate_prediction(json.loads(final_text), review_id)
            result = {
                **prediction,
                "model": MODEL,
                "tool_calls": tool_count,
                "tool_names": tool_names,
                "rounds": round_index,
                "usage": usage,
                "completed_at_utc": utc_now(),
            }
            trace_append(trace_file, {"event": "case_complete", "at": utc_now(), "result": result})
            return result

        conversation.extend(output_items)
        for call in function_calls:
            tool_count += 1
            name = call.get("name", "")
            tool_names.append(name)
            if tool_count > MAX_TOOL_CALLS:
                raise RuntimeError(f"{review_id} exceeded the {MAX_TOOL_CALLS}-call audit limit")
            arguments: dict[str, Any] = {}
            try:
                arguments = json.loads(call.get("arguments", "{}"))
                result = repo.call(name, arguments)
            except Exception as error:  # return tool errors to the reviewer instead of hiding them
                result = {"status": "tool_error", "tool": name, "error": f"{type(error).__name__}: {error}"}
            trace_append(
                trace_file,
                {
                    "event": "function_result",
                    "at": utc_now(),
                    "round": round_index,
                    "call_id": call.get("call_id"),
                    "name": name,
                    "arguments": arguments,
                    "result": result,
                },
            )
            conversation.append(
                {
                    "type": "function_call_output",
                    "call_id": call["call_id"],
                    "output": canonical(result),
                }
            )
    raise RuntimeError(f"{review_id} exceeded {MAX_ROUNDS} model rounds")


def manifest_payload(output_dir: Path, enable_web: bool) -> dict[str, Any]:
    files = [SOURCE, PROMPT_FILE, PROTOCOL_FILE, SCHEMA_FILE, Path(__file__).resolve()]
    return {
        "status": "agentic_development_run",
        "created_at_utc": utc_now(),
        "records": 90,
        "development_data": True,
        "starting_information": "same_label_free_columns_as_human_reviewers",
        "model_configuration": {
            "model": MODEL,
            "endpoint": "/v1/responses",
            "reasoning": {"effort": "low", "mode": "standard"},
            "text_verbosity": "low",
            "max_output_tokens": 3000,
            "max_tool_calls_per_api_response": 40,
            "max_tool_calls_per_case": MAX_TOOL_CALLS,
            "store": False,
            "github_web_search": enable_web,
        },
        "repository_access": {
            "main_repository": "read-only exact anchor commit",
            "history": "anchor and ancestors only",
            "web": "GitHub domains; current content discovery-only",
            "git_cache": safe_rel(GIT_CACHE),
        },
        "excluded": sorted(LABEL_COLUMNS),
        "files": {safe_rel(path): sha256_file(path) for path in files},
        "output_directory": safe_rel(output_dir),
    }


def freeze_manifest(output_dir: Path, enable_web: bool) -> None:
    path = output_dir / "frozen_manifest.json"
    candidate = manifest_payload(output_dir, enable_web)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        comparable_existing = {key: value for key, value in existing.items() if key != "created_at_utc"}
        comparable_candidate = {key: value for key, value in candidate.items() if key != "created_at_utc"}
        if comparable_existing != comparable_candidate:
            raise RuntimeError("Frozen manifest differs from the current implementation; use a new output directory")
        return
    path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_completed(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        validate_prediction(row, row["review_id"])
        completed.add(row["review_id"])
    return completed


def append_prediction(path: Path, result: dict[str, Any]) -> None:
    with WRITE_LOCK:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(canonical(result) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--ids", default="", help="Comma-separated review ids")
    parser.add_argument("--no-web", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "traces").mkdir(parents=True, exist_ok=True)
    prompt = PROMPT_FILE.read_text(encoding="utf-8")
    schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    cases = load_cases()
    if args.ids:
        wanted = {value.strip() for value in args.ids.split(",") if value.strip()}
        cases = [case for case in cases if case["review_id"] in wanted]
        if {case["review_id"] for case in cases} != wanted:
            raise ValueError("One or more requested ids are not in the 90-case source")
    for case in cases:
        RepositoryTools(case)
    if args.dry_run:
        print(f"Dry run verified {len(cases)} cases and their exact anchor snapshots")
        return

    enable_web = not args.no_web
    freeze_manifest(output_dir, enable_web)
    api_key = load_api_key()
    predictions_file = output_dir / "predictions.jsonl"
    completed = load_completed(predictions_file)
    pending = [case for case in cases if case["review_id"] not in completed]
    print(f"Starting {len(pending)} pending agentic reviews; {len(completed)} already complete")
    if not pending:
        return

    failures: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 8))) as executor:
        futures = {
            executor.submit(run_case, case, api_key, prompt, schema, output_dir, enable_web): case["review_id"]
            for case in pending
        }
        done_count = 0
        for future in as_completed(futures):
            review_id = futures[future]
            try:
                result = future.result()
                append_prediction(predictions_file, result)
                done_count += 1
                print(
                    f"{done_count:02d}/{len(pending):02d} {review_id} "
                    f"{result['classification']} tools={result['tool_calls']} rounds={result['rounds']}",
                    flush=True,
                )
            except Exception as error:
                failures.append({"review_id": review_id, "error": f"{type(error).__name__}: {error}"})
                print(f"FAILED {review_id}: {type(error).__name__}: {error}", flush=True)

    if failures:
        (output_dir / "failures.json").write_text(
            json.dumps(failures, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        raise RuntimeError(f"{len(failures)} cases failed; rerun to resume")
    failure_path = output_dir / "failures.json"
    if failure_path.exists():
        failure_path.unlink()
    print(f"Completed {len(pending)} cases; results: {predictions_file}")


if __name__ == "__main__":
    main()
