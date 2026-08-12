#!/usr/bin/env python3
"""Local-first Markdown memory core for T2-T6.

Markdown remains the source of truth. SQLite is a disposable FTS5 cache.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "0.2-draft"
INDEX_DIR = ".memory"
INDEX_DB = "index.sqlite3"
ID_RE = re.compile(r"^[A-Z][A-Z0-9_-]{2,63}$")
# Keep Latin words intact. CJK is handled as overlapping bigrams in the
# fallback ranker because SQLite's default tokenizer does not segment Chinese.
TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]+", re.UNICODE)
EXCLUDED_DIRS = {".git", ".memory", "archive"}


def user_config_path() -> Path:
    """Return a per-user config path; never store this machine path in Git."""
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "ai-knowledge-capture" / "config.json"


class MemoryError(Exception):
    pass


def fail(message: str) -> None:
    raise MemoryError(message)


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"null", "~", ""}:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.startswith("[") and value.endswith("]"):
        try:
            return json.loads(value.replace("'", '"'))
        except json.JSONDecodeError:
            return [part.strip() for part in value[1:-1].split(",") if part.strip()]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?(?:\d+\.\d+|\d+e[+-]?\d+)", value, re.I):
        return float(value)
    return value.strip("\"'")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return {}, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}, text
    metadata: dict[str, Any] = {}
    for line in lines[1:end]:
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = parse_scalar(value)
    body = "\n".join(lines[end + 1:]).lstrip("\n")
    return metadata, body


def first_heading(body: str, fallback: str) -> str:
    for line in body.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip() or fallback
    return fallback


def infer_type(path: Path) -> str:
    lowered = str(path).lower().replace("\\", "/")
    if "decision" in path.name.lower() or "/decisions/" in lowered:
        return "decision"
    if "current-status" in path.name.lower():
        return "state"
    if "/cases/" in lowered or "casebook" in path.name.lower():
        return "case"
    if "/methods/" in lowered or "methodology" in path.name.lower():
        return "knowledge"
    if "/insights/" in lowered:
        return "knowledge"
    if "preferences" in path.name.lower():
        return "preference"
    if "profile" in path.name.lower():
        return "profile"
    return "project"


def infer_project(path: Path, root: Path) -> str | None:
    try:
        relative = path.relative_to(root).as_posix().split("/")
    except ValueError:
        return None
    if len(relative) >= 2 and relative[0] in {"projects", "01-projects"}:
        return relative[1]
    return None


def stable_id(metadata: dict[str, Any], path: Path, root: Path) -> str:
    value = metadata.get("id")
    if isinstance(value, str) and ID_RE.fullmatch(value):
        return value
    digest = hashlib.sha1(path.relative_to(root).as_posix().encode("utf-8")).hexdigest()[:12].upper()
    return f"FILE_{digest}"


def normalize_memory(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    metadata, body = parse_frontmatter(text)
    relative = path.relative_to(root).as_posix()
    stat = path.stat()
    updated = metadata.get("updated_at")
    if not isinstance(updated, str):
        updated = datetime.fromtimestamp(stat.st_mtime, timezone.utc).date().isoformat()
    created = metadata.get("created_at")
    if not isinstance(created, str):
        created = updated
    project = metadata.get("project")
    if not isinstance(project, str):
        project = infer_project(path, root)
    tags = metadata.get("tags")
    if not isinstance(tags, list):
        tags = []
    title = metadata.get("title")
    if not isinstance(title, str) or not title.strip():
        title = first_heading(body, path.stem)
    status = metadata.get("status")
    if status not in {"active", "pending", "superseded", "rejected", "archived"}:
        status = "pending" if relative.startswith("inbox/") else "active"
    scope = metadata.get("scope")
    if scope not in {"formal", "inbox"}:
        scope = "inbox" if relative.startswith("inbox/") else "formal"
    return {
        "id": stable_id(metadata, path, root),
        "type": metadata.get("type") if metadata.get("type") in {
            "profile", "preference", "project", "state", "decision", "knowledge", "case"
        } else infer_type(path),
        "title": title.strip(),
        "created_at": created,
        "updated_at": updated,
        "source": str(metadata.get("source") or relative),
        "project": project,
        "tags": tags,
        "importance": int(metadata.get("importance") or 0),
        "confidence": float(metadata.get("confidence") or 0),
        "status": status,
        "scope": scope,
        "supersedes": metadata.get("supersedes"),
        "superseded_by": metadata.get("superseded_by"),
        "path": relative,
        "content": body,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def markdown_files(root: Path) -> list[Path]:
    if not root.exists():
        fail(f"Knowledge Base does not exist: {root}")
    paths = []
    for path in root.rglob("*.md"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        paths.append(path)
    return sorted(paths)


def db_path(root: Path) -> Path:
    return root / INDEX_DIR / INDEX_DB


def connect(root: Path) -> sqlite3.Connection:
    path = db_path(root)
    if not path.exists():
        fail(f"Index not found: {path}; run memory rebuild-index")
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def ensure_db(root: Path) -> sqlite3.Connection:
    root.joinpath(INDEX_DIR).mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path(root))
    con.executescript("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            path TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            project TEXT,
            status TEXT NOT NULL,
            scope TEXT NOT NULL,
            importance INTEGER NOT NULL,
            confidence REAL NOT NULL,
            updated_at TEXT NOT NULL,
            source TEXT NOT NULL,
            tags TEXT NOT NULL,
            content TEXT NOT NULL,
            sha256 TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
            id UNINDEXED, title, project, tags, content
        );
    """)
    return con


def rebuild_index(root: Path) -> dict[str, Any]:
    con = ensure_db(root)
    try:
        con.execute("DELETE FROM memories")
        con.execute("DELETE FROM memories_fts")
        records = []
        for path in markdown_files(root):
            record = normalize_memory(path, root)
            records.append(record)
            con.execute(
                """INSERT INTO memories
                (id,path,type,title,project,status,scope,importance,confidence,updated_at,source,tags,content,sha256)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    record["id"], record["path"], record["type"], record["title"],
                    record["project"], record["status"], record["scope"],
                    record["importance"], record["confidence"], record["updated_at"],
                    record["source"], json.dumps(record["tags"], ensure_ascii=False),
                    record["content"], record["sha256"],
                ),
            )
            con.execute(
                "INSERT INTO memories_fts(id,title,project,tags,content) VALUES (?,?,?,?,?)",
                (
                    record["id"], record["title"], record["project"] or "",
                    " ".join(record["tags"]), record["content"],
                ),
            )
        con.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version',?)", (SCHEMA_VERSION,))
        con.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('built_at',?)", (datetime.now(timezone.utc).isoformat(),))
        con.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('root',?)", (str(root),))
        con.commit()
        return {"indexed": len(records), "database": str(db_path(root)), "schema_version": SCHEMA_VERSION}
    finally:
        con.close()


def query_terms(query: str) -> list[str]:
    terms: list[str] = []
    for token in TOKEN_RE.findall(query.lower()):
        if re.fullmatch(r"[\u4e00-\u9fff]+", token):
            if len(token) < 2:
                terms.append(token)
            else:
                terms.extend(token[index:index + 2] for index in range(len(token) - 1))
        else:
            terms.append(token)
    return list(dict.fromkeys(terms))


def search_records(root: Path, query: str, project: str | None = None, active_only: bool = False, limit: int = 10) -> list[dict[str, Any]]:
    terms = query_terms(query)
    if not terms:
        return []
    con = connect(root)
    try:
        match = " OR ".join(f'"{term}"' for term in terms)
        rows = con.execute(
            """SELECT m.*, bm25(memories_fts) AS fts_score
               FROM memories_fts
               JOIN memories m ON m.id = memories_fts.id
               WHERE memories_fts MATCH ?""",
            (match,),
        ).fetchall()
    except sqlite3.OperationalError:
        rows = []
    finally:
        con.close()
    results = []
    query_lower = query.lower()
    if not rows:
        # SQLite's default tokenizer is intentionally conservative for CJK text.
        # Fall back to deterministic substring matching so Chinese queries remain usable
        # without introducing a tokenizer or embedding dependency in T2-T3.
        con = connect(root)
        try:
            rows = con.execute("SELECT * FROM memories").fetchall()
        finally:
            con.close()
    for row in rows:
        item = dict(row)
        if project and item["project"] != project:
            continue
        if active_only and item["status"] != "active":
            continue
        haystack = " ".join(str(item.get(key) or "") for key in ("title", "project", "tags", "content")).lower()
        hits = sum(haystack.count(term) for term in terms)
        if not hits:
            continue
        score = hits + (4 if project and item["project"] == project else 0)
        score += min(item["importance"], 10) / 10
        score += min(item["confidence"], 1)
        score += 1 if item["status"] == "active" else -2
        item["relevance_score"] = round(score, 3)
        item["match_reason"] = "keyword match"
        if project and item["project"] == project:
            item["match_reason"] = "same project + keyword match"
        results.append(item)
    results.sort(key=lambda item: (-item["relevance_score"], item["updated_at"], item["id"]), reverse=False)
    return results[:limit]


def compact(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"], "type": item["type"], "title": item["title"],
        "path": item["path"], "project": item["project"],
        "status": item["status"], "confidence": item["confidence"],
        "importance": item["importance"], "updated_at": item["updated_at"],
        "relevance_score": item.get("relevance_score"),
        "match_reason": item.get("match_reason"),
        "source": item["source"],
    }


def context_builder(results: list[dict[str, Any]], token_budget: int = 2400) -> tuple[str, list[dict[str, Any]]]:
    ordered = sorted(
        [item for item in results if item["status"] == "active"],
        key=lambda item: (
            {"state": 0, "decision": 1, "project": 2, "preference": 3, "profile": 4, "knowledge": 5, "case": 6}.get(item["type"], 9),
            -float(item.get("relevance_score") or 0),
        ),
    )
    sections = {
        "project": "Current Project",
        "decision": "Active Decisions",
        "state": "Current State",
        "preference": "Preferences",
        "profile": "Profile",
        "knowledge": "Related Knowledge",
        "case": "Related Cases",
    }
    lines = ["# Relevant User Context", ""]
    included = []
    used = 0
    for item in ordered:
        body = re.sub(r"\s+", " ", item["content"]).strip()
        if not body:
            body = item["title"]
        snippet = body[:900]
        block = f"## {sections.get(item['type'], 'Related Knowledge')}\\n- {item['title']} ({item['path']})\\n- {snippet}\\n- score: {item.get('relevance_score')}\\n- reason: {item.get('match_reason')}\\n"
        if used + len(block) > token_budget * 4:
            continue
        lines.append(block)
        included.append(compact(item))
        used += len(block)
    if len(lines) == 1:
        lines.append("No relevant active context found.")
    return "\n".join(lines), included


def resolve_root(value: str | None) -> Path:
    candidate = value or os.environ.get("MEMORY_KB_ROOT")
    if not candidate:
        config_path = user_config_path()
        if config_path.exists():
            try:
                candidate = json.loads(config_path.read_text(encoding="utf-8")).get("root")
            except (OSError, json.JSONDecodeError) as exc:
                fail(f"Cannot read local setup config {config_path}: {exc}")
    if not candidate:
        fail("首次使用：请让 Agent 询问你的知识库目录，然后运行 memory setup <目录>")
    root = Path(candidate).expanduser().resolve()
    if not root.exists():
        fail(f"Knowledge Base does not exist: {root}")
    if not os.access(root, os.R_OK):
        fail(f"Knowledge Base is not readable: {root}")
    return root


def command_setup(root_value: str) -> dict[str, Any]:
    root = Path(root_value).expanduser().resolve()
    if not root.exists():
        try:
            root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            fail(f"Cannot create Knowledge Base directory {root}: {exc}")
    if not os.access(root, os.R_OK):
        fail(f"Knowledge Base directory is not readable: {root}")
    if not os.access(root, os.W_OK):
        fail(f"Knowledge Base directory is not writable: {root}")
    config_path = user_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps({"root": str(root), "schema_version": SCHEMA_VERSION}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = command_init(root)
    return {
        "status": "ready",
        "message": "知识库已准备完成",
        "root": str(root),
        "config": str(config_path),
        "index": result,
        "next": "以后直接用自然语言让 Agent 查询或沉淀知识。",
    }


def command_init(root: Path) -> dict[str, Any]:
    root.joinpath(INDEX_DIR).mkdir(parents=True, exist_ok=True)
    return rebuild_index(root)


def command_inspect(root: Path, memory_id: str) -> dict[str, Any]:
    con = connect(root)
    try:
        row = con.execute("SELECT * FROM memories WHERE id=?", (memory_id,)).fetchone()
    finally:
        con.close()
    if row is None:
        fail(f"Memory not found: {memory_id}")
    item = dict(row)
    item["tags"] = json.loads(item["tags"])
    return item


def find_memory_path(root: Path, memory_id: str) -> tuple[Path, dict[str, Any]]:
    item = command_inspect(root, memory_id)
    path = root / item["path"]
    if not path.exists():
        fail(f"Indexed memory file does not exist: {path}")
    return path, item


def rewrite_frontmatter(path: Path, updates: dict[str, Any], body: str | None = None) -> None:
    text = path.read_text(encoding="utf-8")
    metadata, existing_body = parse_frontmatter(text)
    if not metadata:
        fail(f"Cannot lifecycle-update Markdown without frontmatter: {path}")
    metadata.update(updates)
    lines = ["---"]
    for key, value in metadata.items():
        if isinstance(value, list):
            encoded = "[" + ", ".join(str(item) for item in value) + "]"
        elif value is None:
            encoded = "null"
        else:
            encoded = str(value)
        lines.append(f"{key}: {encoded}")
    lines.extend(["---", "", existing_body if body is None else body.rstrip(), ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def command_update_state(root: Path, memory_id: str, body_file: Path) -> dict[str, Any]:
    path, item = find_memory_path(root, memory_id)
    if item["type"] != "state":
        fail(f"UPDATE state requires type=state, got {item['type']}")
    if not body_file.exists():
        fail(f"State body file does not exist: {body_file}")
    body = body_file.read_text(encoding="utf-8")
    rewrite_frontmatter(path, {"updated_at": date.today().isoformat(), "status": "active", "scope": "formal"}, body)
    rebuild_index(root)
    return {"action": "UPDATE", "id": memory_id, "path": str(path.relative_to(root)), "status": "active"}


def command_supersede(root: Path, old_id: str, new_id: str) -> dict[str, Any]:
    if old_id == new_id:
        fail("SUPERSEDE requires two different memory IDs")
    old_path, old = find_memory_path(root, old_id)
    new_path, new = find_memory_path(root, new_id)
    if old["status"] != "active" or old["scope"] != "formal":
        fail(f"Old memory must be active: {old_id} is {old['status']}")
    if new["status"] != "active" or new["scope"] != "formal":
        fail(f"New memory must be active formal memory: {new_id}")
    rewrite_frontmatter(old_path, {"status": "superseded", "scope": "formal", "superseded_by": new_id})
    rewrite_frontmatter(new_path, {"supersedes": old_id, "status": "active", "scope": "formal"})
    rebuild_index(root)
    return {"action": "SUPERSEDE", "old_id": old_id, "new_id": new_id, "old_status": "superseded"}


def command_merge(root: Path, source_id: str, target_id: str) -> dict[str, Any]:
    if source_id == target_id:
        fail("MERGE requires two different memory IDs")
    source_path, source = find_memory_path(root, source_id)
    target_path, target = find_memory_path(root, target_id)
    if source["status"] != "active" or target["status"] != "active":
        fail("MERGE requires two active memories")
    if source["type"] != target["type"] or source["project"] != target["project"]:
        fail("MERGE requires matching type and project")
    target_body = target["content"].rstrip()
    source_body = source["content"].strip()
    merged = f"{target_body}\n\n## Merged source: {source['title']}\n\n{source_body}\n"
    rewrite_frontmatter(target_path, {"updated_at": date.today().isoformat()}, merged)
    rewrite_frontmatter(source_path, {"status": "archived", "scope": "formal", "merged_into": target_id})
    rebuild_index(root)
    return {"action": "MERGE", "source_id": source_id, "target_id": target_id, "source_status": "archived"}


def command_status(root: Path) -> dict[str, Any]:
    con = connect(root)
    try:
        total = con.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        by_status = {row[0]: row[1] for row in con.execute("SELECT status,COUNT(*) FROM memories GROUP BY status")}
        by_type = {row[0]: row[1] for row in con.execute("SELECT type,COUNT(*) FROM memories GROUP BY type")}
        meta = {row[0]: row[1] for row in con.execute("SELECT key,value FROM meta")}
    finally:
        con.close()
    return {"root": str(root), "database": str(db_path(root)), "total": total, "by_status": by_status, "by_type": by_type, "meta": meta}


def command_doctor(root: Path) -> dict[str, Any]:
    checks = {"root_readable": os.access(root, os.R_OK), "root_writable": os.access(root, os.W_OK), "fts5": False, "index": db_path(root).exists()}
    try:
        con = sqlite3.connect(":memory:")
        con.execute("CREATE VIRTUAL TABLE t USING fts5(content)")
        checks["fts5"] = True
        con.close()
    except sqlite3.Error:
        checks["fts5"] = False
    if checks["index"]:
        checks["indexed_files"] = command_status(root)["total"]
    checks["ok"] = all(value for key, value in checks.items() if key not in {"indexed_files"})
    return checks


def active_catalog(root: Path) -> dict[str, dict[str, Any]]:
    con = connect(root)
    try:
        rows = con.execute("SELECT * FROM memories").fetchall()
    finally:
        con.close()
    return {row["id"]: dict(row) for row in rows}


def command_benchmark(root: Path, fixture: Path) -> dict[str, Any]:
    data = json.loads(fixture.read_text(encoding="utf-8"))
    catalog = active_catalog(root)
    fixture_ids = {item["id"] for item in data["memory_catalog"]}
    missing_ids = sorted(fixture_ids - set(catalog))
    if missing_ids:
        return {
            "benchmark_version": data["benchmark_version"],
            "status": "not_applicable",
            "reason": "Knowledge Base does not contain benchmark fixture IDs",
            "missing_fixture_ids": missing_ids,
            "metrics": None,
            "cases": [],
        }
    outcomes = []
    for case in data["cases"]:
        results = search_records(root, case["query"], case["context"].get("project"), active_only=True, limit=20)
        selected = [item["id"] for item in results]
        required = set(case["expected_relevant_ids"])
        allowed = set(case["allowed_ids"])
        forbidden = set(case["forbidden_ids"])
        injected = set(selected)
        recall_hit = required.issubset(injected)
        wrong = sorted(injected - allowed)
        pollution = sorted((injected & forbidden) | {
            memory_id for memory_id in injected
            if memory_id in catalog and catalog[memory_id]["status"] != "active"
        })
        outcomes.append({
            "id": case["id"], "recall_hit": recall_hit,
            "wrong_recall": wrong, "context_pollution": pollution,
            "returned_ids": selected,
        })
    return {
        "benchmark_version": data["benchmark_version"],
        "status": "completed",
        "metrics": {
            "recall_hit": all(item["recall_hit"] for item in outcomes),
            "wrong_recall": sum(len(item["wrong_recall"]) for item in outcomes),
            "context_pollution": sum(len(item["context_pollution"]) for item in outcomes),
        },
        "cases": outcomes,
    }


def command_debug(root: Path, query: str, project: str | None, token_budget: int) -> dict[str, Any]:
    candidates = search_records(root, query, project, active_only=False, limit=50)
    context, included = context_builder(candidates, token_budget)
    included_ids = {item["id"] for item in included}
    return {
        "query": query,
        "project": project,
        "candidate_count": len(candidates),
        "candidates": [compact(item) for item in candidates],
        "injected": included,
        "excluded": [compact(item) for item in candidates if item["id"] not in included_ids],
        "context": context,
        "rules": {"active_only": True, "superseded_excluded": True, "pending_excluded": True, "token_budget": token_budget},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="memory", description="Markdown-native local memory core")
    parser.add_argument("--root", help="Knowledge Base root; or use MEMORY_KB_ROOT")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    sub = parser.add_subparsers(dest="command", required=True)
    setup = sub.add_parser("setup", help="首次设置知识库并自动初始化")
    setup.add_argument("root")
    sub.add_parser("init")
    sub.add_parser("rebuild-index")
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--project")
    search.add_argument("--limit", type=int, default=10)
    recall = sub.add_parser("recall")
    recall.add_argument("query")
    recall.add_argument("--project")
    recall.add_argument("--token-budget", type=int, default=2400)
    inspect = sub.add_parser("inspect")
    inspect.add_argument("memory_id")
    sub.add_parser("status")
    sub.add_parser("doctor")
    benchmark = sub.add_parser("benchmark")
    benchmark.add_argument("--fixture", default=str(Path("evals") / "recall-benchmark.json"))
    debug = sub.add_parser("debug")
    debug.add_argument("query")
    debug.add_argument("--project")
    debug.add_argument("--token-budget", type=int, default=2400)
    update_state = sub.add_parser("update-state")
    update_state.add_argument("memory_id")
    update_state.add_argument("--body-file", required=True)
    supersede = sub.add_parser("supersede")
    supersede.add_argument("old_id")
    supersede.add_argument("new_id")
    merge = sub.add_parser("merge")
    merge.add_argument("source_id")
    merge.add_argument("target_id")

    args = parser.parse_args(argv)
    if args.command == "setup":
        result = command_setup(args.root)
    else:
        root = resolve_root(args.root)
    if args.command in {"init", "rebuild-index"}:
        result = command_init(root) if args.command == "init" else rebuild_index(root)
    elif args.command == "search":
        result = [compact(item) for item in search_records(root, args.query, args.project, False, args.limit)]
    elif args.command == "recall":
        results = search_records(root, args.query, args.project, True, 50)
        context, included = context_builder(results, args.token_budget)
        result = {"context": context, "memories": included}
    elif args.command == "inspect":
        result = command_inspect(root, args.memory_id)
    elif args.command == "status":
        result = command_status(root)
    elif args.command == "doctor":
        result = command_doctor(root)
    elif args.command == "benchmark":
        fixture_path = Path(args.fixture)
        if not fixture_path.is_absolute():
            fixture_path = Path(__file__).resolve().parents[1] / fixture_path
        result = command_benchmark(root, fixture_path)
    elif args.command == "debug":
        result = command_debug(root, args.query, args.project, args.token_budget)
    elif args.command == "update-state":
        result = command_update_state(root, args.memory_id, Path(args.body_file))
    elif args.command == "supersede":
        result = command_supersede(root, args.old_id, args.new_id)
    elif args.command == "merge":
        result = command_merge(root, args.source_id, args.target_id)
    elif args.command != "setup":
        fail(f"Unsupported command: {args.command}")
    if args.json or args.command in {"setup", "init", "rebuild-index", "search", "recall", "inspect", "status", "doctor", "benchmark", "debug", "update-state", "supersede", "merge"}:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (MemoryError, OSError, sqlite3.Error, json.JSONDecodeError) as exc:
        print(f"memory: error: {exc}", file=sys.stderr)
        raise SystemExit(2)
