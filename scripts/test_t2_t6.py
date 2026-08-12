#!/usr/bin/env python3
"""Integration checks for T2-T6 using a temporary Markdown knowledge base."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import memory


def write_memory(root: Path, memory_id: str, memory_type: str, title: str, project: str, status: str, body: str, superseded_by: str | None = None) -> None:
    path = root / "projects" / project / f"{memory_id.lower()}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join([
            "---",
            f"id: {memory_id}",
            f"type: {memory_type}",
            f"title: {title}",
            "created_at: 2026-08-12",
            "updated_at: 2026-08-12",
            "source: fixture",
            f"project: {project}",
            "tags: [fixture]",
            "importance: 8",
            "confidence: 0.9",
            f"status: {status}",
            "scope: formal",
            "supersedes: null",
            f"superseded_by: {superseded_by or 'null'}",
            "---",
            "",
            body,
            "",
        ]),
        encoding="utf-8",
    )


def main() -> int:
    fixture_path = Path(__file__).resolve().parents[1] / "evals" / "recall-benchmark.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    root = Path(tempfile.mkdtemp(prefix="memory-t2-t6-"))
    try:
        write_memory(root, "PROJ-OPEN-MEMORY-001", "project", "跨 Agent Memory Skill", "open-memory", "active", "Markdown 作为事实源，下一步验证跨 Agent Recall。")
        write_memory(root, "DEC-OPEN-MEMORY-MARKDOWN-001", "decision", "Markdown 作为事实源", "open-memory", "active", "Markdown 是事实源，索引可以重建。")
        write_memory(root, "STATE-OPEN-MEMORY-RECALL-001", "state", "下一步验证跨 Agent Recall", "open-memory", "active", "下一步验证跨 Agent Recall。")
        write_memory(root, "DEC-SHOPMEMO-BRAND-001", "decision", "一个 Project 对应一个品牌", "shopmemo", "active", "一个 Project 对应一个品牌，因为品牌记忆和反馈需要隔离。")
        write_memory(root, "STATE-SHOPMEMO-DRAFT-001", "state", "ShopMemo 正在开发", "shopmemo", "superseded", "旧状态。", "STATE-SHOPMEMO-LAUNCH-001")
        write_memory(root, "STATE-SHOPMEMO-LAUNCH-001", "state", "ShopMemo 已完成核心功能并进入冷启动", "shopmemo", "active", "核心功能已完成，下一步是真实用户冷启动。")
        write_memory(root, "DEC-SHOPMEMO-ENGLISH-001", "decision", "优先做英文市场", "shopmemo", "superseded", "旧决策。", "DEC-SHOPMEMO-CHINESE-001")
        write_memory(root, "DEC-SHOPMEMO-CHINESE-001", "decision", "改为中文市场优先", "shopmemo", "active", "当前优先中文市场。")
        write_memory(root, "PROJ-TEMU-001", "project", "TEMU 商品机会研究", "temu", "active", "TEMU 研究。")
        write_memory(root, "DEC-TEMU-SEO-001", "knowledge", "TEMU SEO 关键词研究", "temu", "active", "TEMU SEO。")
        memory.rebuild_index(root)
        status = memory.command_status(root)
        assert status["total"] == 10
        recalls = []
        for case in fixture["cases"]:
            results = memory.search_records(root, case["query"], case["context"].get("project"), active_only=True, limit=20)
            ids = {item["id"] for item in results}
            recalls.append({
                "id": case["id"],
                "hit": set(case["expected_relevant_ids"]) <= ids,
                "wrong": sorted(ids - set(case["allowed_ids"])),
                "pollution": sorted((ids & set(case["forbidden_ids"])) | {
                    item["id"] for item in results if item["status"] != "active"
                }),
            })
        # The harness proves the mechanics and reports any fixture/query mismatch honestly.
        if any(row["wrong"] for row in recalls):
            print(json.dumps({"recall_debug": recalls}, ensure_ascii=False, indent=2))
            raise AssertionError("wrong recall detected")
        update_body = root / "updated.md"
        update_body.write_text("核心功能完成，进入冷启动验证。", encoding="utf-8")
        memory.command_update_state(root, "STATE-SHOPMEMO-LAUNCH-001", update_body)
        write_memory(root, "DEC-SHOPMEMO-PRIORITY-001", "decision", "暂定市场优先级", "shopmemo", "active", "旧市场优先级。")
        write_memory(root, "DEC-SHOPMEMO-PRIORITY-002", "decision", "新的市场优先级", "shopmemo", "active", "新市场优先级。")
        memory.rebuild_index(root)
        supersede_result = memory.command_supersede(root, "DEC-SHOPMEMO-PRIORITY-001", "DEC-SHOPMEMO-PRIORITY-002")
        write_memory(root, "KNOWLEDGE-SHOPMEMO-MERGE-001", "knowledge", "方法片段 A", "shopmemo", "active", "方法片段 A。")
        write_memory(root, "KNOWLEDGE-SHOPMEMO-MERGE-002", "knowledge", "方法片段 B", "shopmemo", "active", "方法片段 B。")
        memory.rebuild_index(root)
        merge_result = memory.command_merge(root, "KNOWLEDGE-SHOPMEMO-MERGE-001", "KNOWLEDGE-SHOPMEMO-MERGE-002")
        report = {"indexed": status["total"], "recall_cases": recalls, "lifecycle": ["UPDATE", supersede_result, merge_result], "fts5": memory.command_doctor(root)["fts5"]}
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
