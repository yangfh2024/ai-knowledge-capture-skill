#!/usr/bin/env python3
"""Validate the T1 protocol fixtures without SQLite or third-party packages."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "system" / "schemas"
EVAL_DIR = ROOT / "evals"


class ValidationError(Exception):
    pass


def load_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:
        raise ValidationError(f"{path}: invalid JSON: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_memory_item(item: dict) -> None:
    required = {
        "id", "type", "title", "created_at", "updated_at", "source",
        "project", "tags", "importance", "confidence", "status",
        "scope", "supersedes", "superseded_by",
    }
    require(required <= item.keys(), "memory item missing required field")
    require(item["type"] in {
        "profile", "preference", "project", "state",
        "decision", "knowledge", "case",
    }, f"unsupported memory type: {item['type']}")
    require(item["scope"] in {"formal", "inbox"}, "invalid memory scope")
    require(0 <= item["importance"] <= 10, "importance outside 0..10")
    require(0 <= item["confidence"] <= 1, "confidence outside 0..1")
    require(item["created_at"] <= item["updated_at"], "updated_at before created_at")
    if item["scope"] == "inbox":
        require(item["status"] == "pending", "Inbox item must be pending")
    if item["status"] == "pending":
        require(item["scope"] == "inbox", "pending item must be in Inbox")
    if item["status"] == "superseded":
        require(item["scope"] == "formal", "superseded item must be formal")
        require(isinstance(item["superseded_by"], str), "superseded item needs superseded_by")
    if item["status"] == "active":
        require(item["superseded_by"] is None, "active item cannot have superseded_by")


def assert_invalid_memory_item(item: dict, label: str) -> None:
    try:
        validate_memory_item(item)
    except ValidationError:
        return
    raise ValidationError(f"{label}: invalid lifecycle state was accepted")


def validate_gate_fixture(test: dict) -> None:
    action = test["action"]
    proposal = test
    target = proposal["target"]
    existing_ids = target["existing_ids"]
    require(action == proposal["expected"]["action"], f"{test['id']}: expected action mismatch")
    if action == "CREATE":
        require(not existing_ids, f"{test['id']}: CREATE cannot target existing IDs")
    elif action == "UPDATE":
        require(len(existing_ids) >= 1, f"{test['id']}: UPDATE needs one existing ID")
    elif action == "MERGE":
        require(len(existing_ids) >= 2, f"{test['id']}: MERGE needs at least two IDs")
    elif action == "IGNORE":
        require(target["path"] is None, f"{test['id']}: IGNORE cannot have a target path")
    elif action == "SUPERSEDE":
        require(len(existing_ids) >= 1, f"{test['id']}: SUPERSEDE needs an old ID")
        require(proposal["candidate"]["type"] == "decision", f"{test['id']}: SUPERSEDE fixture must be a decision")
        require(target["superseded_by"] is None, f"{test['id']}: proposal cannot pre-fill superseded_by")
    else:
        raise ValidationError(f"{test['id']}: unknown gate action {action}")
    require(proposal["candidate"]["status"] == "pending", f"{test['id']}: candidate must be pending")
    require(proposal["approval_status"] == "pending", f"{test['id']}: fixture must await approval")


def evaluate_recall(case: dict, catalog: dict[str, dict]) -> tuple[int, int, int]:
    clean = case["clean_result"]
    returned = set(clean["returned_ids"])
    injected = set(clean["injected_ids"])
    required = set(case["expected_relevant_ids"])
    allowed = set(case["allowed_ids"])
    forbidden = set(case["forbidden_ids"])
    recall_hit = int(required <= returned)
    wrong_recall = len(returned - allowed)
    inactive = {
        memory_id for memory_id in injected
        if memory_id in catalog and catalog[memory_id]["status"] != "active"
    }
    pollution = len((injected & forbidden) | inactive)
    require(recall_hit == 1, f"{case['id']}: clean fixture misses required memory")
    require(wrong_recall == 0, f"{case['id']}: clean fixture has wrong recall")
    require(pollution == 0, f"{case['id']}: clean fixture has context pollution")

    wrong_probe = set(case["wrong_recall_probe"]["returned_ids"])
    require(len(wrong_probe - allowed) > 0, f"{case['id']}: wrong-recall probe is not discriminating")
    pollution_probe = set(case["pollution_probe"]["injected_ids"])
    probe_pollution = (pollution_probe & forbidden) | {
        memory_id for memory_id in pollution_probe
        if memory_id in catalog and catalog[memory_id]["status"] != "active"
    }
    require(probe_pollution, f"{case['id']}: pollution probe does not contain a forbidden/inactive memory")
    return recall_hit, wrong_recall, pollution


def main() -> int:
    schema_paths = [
        SCHEMA_DIR / "memory-item.schema.json",
        SCHEMA_DIR / "memory-proposal.schema.json",
        SCHEMA_DIR / "recall-benchmark.schema.json",
    ]
    for schema_path in schema_paths:
        schema = load_json(schema_path)
        require(schema.get("$schema"), f"{schema_path}: missing $schema")
        require(schema.get("type") == "object", f"{schema_path}: root must be object")
    print(f"[PASS] parsed {len(schema_paths)} machine schemas")

    template = (ROOT / "templates" / "memory-item.md").read_text(encoding="utf-8")
    required_frontmatter = [
        "id:", "type:", "title:", "created_at:", "updated_at:", "source:",
        "project:", "tags:", "importance:", "confidence:", "status:",
        "scope:", "supersedes:", "superseded_by:",
    ]
    require(all(field in template for field in required_frontmatter), "frontmatter template missing required field")
    print(f"[PASS] frontmatter template contains {len(required_frontmatter)} required fields")

    valid_items = [
        {
            "id": "STATE-DEMO-001", "type": "state", "title": "Demo state",
            "created_at": "2026-08-11", "updated_at": "2026-08-11", "source": "fixture",
            "project": "demo", "tags": ["fixture"], "importance": 5, "confidence": 0.8,
            "status": "active", "scope": "formal", "supersedes": None, "superseded_by": None,
        },
        {
            "id": "DEC-DEMO-001", "type": "decision", "title": "Demo pending decision",
            "created_at": "2026-08-11", "updated_at": "2026-08-11", "source": "fixture",
            "project": "demo", "tags": ["fixture"], "importance": 6, "confidence": 0.6,
            "status": "pending", "scope": "inbox", "supersedes": None, "superseded_by": None,
        },
        {
            "id": "DEC-DEMO-002", "type": "decision", "title": "Demo superseded decision",
            "created_at": "2026-08-11", "updated_at": "2026-08-11", "source": "fixture",
            "project": "demo", "tags": ["fixture"], "importance": 6, "confidence": 0.6,
            "status": "superseded", "scope": "formal", "supersedes": None, "superseded_by": "DEC-DEMO-003",
        },
    ]
    for item in valid_items:
        validate_memory_item(item)
    invalid_pending = dict(valid_items[0], status="pending")
    invalid_superseded = dict(valid_items[0], status="superseded")
    invalid_active_link = dict(valid_items[0], superseded_by="DEC-DEMO-003")
    assert_invalid_memory_item(invalid_pending, "formal pending")
    assert_invalid_memory_item(invalid_superseded, "superseded without link")
    assert_invalid_memory_item(invalid_active_link, "active with superseded_by")
    print("[PASS] lifecycle rules reject invalid active/pending/superseded combinations")

    gate = load_json(EVAL_DIR / "memory-gate-fixtures.json")
    actions = [test["action"] for test in gate["tests"]]
    require(set(actions) == {"CREATE", "UPDATE", "MERGE", "IGNORE", "SUPERSEDE"}, "gate fixtures must cover exactly five actions")
    require(len(actions) == 5, "gate fixtures must contain one sample per action")
    for test in gate["tests"]:
        validate_gate_fixture(test)
    print("[PASS] Memory Gate: CREATE / UPDATE / MERGE / IGNORE / SUPERSEDE")

    recall = load_json(EVAL_DIR / "recall-benchmark.json")
    require(recall["benchmark_version"] == "0.2", "unexpected benchmark version")
    require(set(recall["metrics"]) == {"recall_hit", "wrong_recall", "context_pollution"}, "three recall metrics missing")
    cases = recall["cases"]
    require(len(cases) == 5, "Recall Benchmark must contain five cases")
    catalog = {item["id"]: item for item in recall["memory_catalog"]}
    totals = [0, 0, 0]
    for case in cases:
        require(set(case["expected_relevant_ids"]) <= set(catalog), f"{case['id']}: unknown required memory")
        require(set(case["forbidden_ids"]) <= set(catalog), f"{case['id']}: unknown forbidden memory")
        require(set(case["expected_relevant_ids"]).isdisjoint(case["forbidden_ids"]), f"{case['id']}: required and forbidden overlap")
        scores = evaluate_recall(case, catalog)
        totals = [left + right for left, right in zip(totals, scores)]
    print(f"[PASS] Recall Benchmark: {len(cases)} cases; clean hit={totals[0]}/{len(cases)}, wrong=0, pollution=0")
    print("[PASS] Negative probes detect wrong recall and context pollution")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        raise SystemExit(1)
