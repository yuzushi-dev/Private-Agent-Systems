import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.token_saving_audit import (
    Audit,
    aggregate_claude_mem,
    aggregate_claude_project_memory,
    aggregate_context_mode_stats,
    estimate_tokens,
    parse_human_number,
    parse_rtk_gain,
    static_context_footprint,
    write_markdown,
)


class TokenSavingAuditTest(unittest.TestCase):
    def test_parse_human_number_supports_suffixes(self):
        self.assertEqual(parse_human_number("23.8M"), 23_800_000)
        self.assertEqual(parse_human_number("640.8K"), 640_800)
        self.assertEqual(parse_human_number("22836"), 22_836)

    def test_parse_rtk_gain_summary(self):
        output = """
RTK Token Savings (Global Scope)
Total commands:    22836
Input tokens:      37.4M
Output tokens:     13.6M
Tokens saved:      23.8M (63.7%)
"""
        summary = parse_rtk_gain(output)
        self.assertEqual(summary["commands"], 22_836)
        self.assertEqual(summary["input_tokens"], 37_400_000)
        self.assertEqual(summary["output_tokens"], 13_600_000)
        self.assertEqual(summary["tokens_saved"], 23_800_000)
        self.assertEqual(summary["reduction_pct"], 63.7)

    def test_context_mode_aggregation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for idx, payload in enumerate(
                [
                    {
                        "total_calls": 2,
                        "bytes_returned": 100,
                        "kept_out": 300,
                        "total_processed": 400,
                        "tokens_saved": 75,
                        "dollars_saved_session": 0.5,
                        "reduction_pct": 75.0,
                    },
                    {
                        "total_calls": 1,
                        "bytes_returned": 50,
                        "kept_out": 50,
                        "total_processed": 100,
                        "tokens_saved": 13,
                        "dollars_saved_session": 0.1,
                        "reduction_pct": 50.0,
                    },
                ]
            ):
                (root / f"stats-pid-{idx}.json").write_text(json.dumps(payload))

            summary = aggregate_context_mode_stats(root)

        self.assertEqual(summary["files"], 2)
        self.assertEqual(summary["total_calls"], 3)
        self.assertEqual(summary["bytes_returned"], 150)
        self.assertEqual(summary["kept_out"], 350)
        self.assertEqual(summary["tokens_saved"], 88)
        self.assertEqual(summary["avg_reduction_pct"], 62.5)

    def test_static_context_footprint_counts_always_on_and_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            codex = home / ".codex"
            claude = home / ".claude"
            vault = home / "Obsidian" / "AgentMemory"
            (codex / "skills" / "a").mkdir(parents=True)
            (claude / "skills" / "b").mkdir(parents=True)
            vault.mkdir(parents=True)
            (codex / "AGENTS.md").write_text("codex agents")
            (claude / "CLAUDE.md").write_text("claude instructions")
            (codex / "RTK.md").write_text("rtk")
            (vault / "AGENTS.md").write_text("vault agents")
            (vault / "CLAUDE.md").write_text("vault claude")
            (codex / "skills" / "a" / "SKILL.md").write_text("x" * 40)
            (claude / "skills" / "b" / "SKILL.md").write_text("y" * 80)

            summary = static_context_footprint(codex, claude, vault)

        self.assertEqual(summary["codex_skill_count"], 1)
        self.assertEqual(summary["claude_skill_count"], 1)
        self.assertEqual(summary["codex_skills_est_tokens"], estimate_tokens("x" * 40))
        self.assertEqual(summary["claude_skills_est_tokens"], estimate_tokens("y" * 80))
        self.assertGreater(summary["always_on_est_tokens"], 0)

    def test_claude_project_memory_counts_memory_files_without_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            claude = Path(tmp) / ".claude"
            first = claude / "projects" / "project-a" / "memory"
            second = claude / "projects" / "project-b" / "memory"
            first.mkdir(parents=True)
            second.mkdir(parents=True)
            (first / "MEMORY.md").write_text("a" * 40)
            (second / "MEMORY.md").write_text("b" * 80)

            summary = aggregate_claude_project_memory(claude)

        self.assertTrue(summary["available"])
        self.assertEqual(summary["memory_file_count"], 2)
        self.assertEqual(summary["memory_est_tokens"], estimate_tokens("a" * 40) + estimate_tokens("b" * 80))
        self.assertEqual(len(summary["memory_files"]), 2)
        self.assertIn("path", summary["memory_files"][0])
        self.assertNotIn("content", summary["memory_files"][0])

    def test_claude_mem_detects_external_installation_without_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            claude = home / ".claude"
            claude_mem = home / ".claude-mem"
            claude_mem.mkdir()
            (claude_mem / "settings.json").write_text('{"dataDir":"memory-data"}')
            data_dir = claude_mem / "memory-data"
            data_dir.mkdir()
            (data_dir / "memory.db").write_bytes(b"x" * 1024)
            plugins = claude / "plugins"
            plugins.mkdir(parents=True)
            (plugins / "installed_plugins.json").write_text(
                json.dumps(
                    {
                        "plugins": {
                            "claude-mem@thedotmack": [
                                {"version": "1.0.0", "scope": "user"}
                            ]
                        }
                    }
                )
            )

            summary = aggregate_claude_mem(home, claude)

        self.assertTrue(summary["available"])
        self.assertTrue(summary["settings_present"])
        self.assertTrue(summary["plugin_present"])
        self.assertEqual(summary["data_file_count"], 2)
        self.assertEqual(summary["data_bytes"], 1024 + len('{"dataDir":"memory-data"}'))
        self.assertEqual(summary["installed_plugins"][0]["name"], "claude-mem@thedotmack")
        self.assertNotIn("content", summary["data_files"][0])

    def test_markdown_redacts_local_details_by_default(self):
        audit = Audit(
            rtk={"available": True},
            context_mode={},
            claude_mem={
                "root_present": True,
                "settings_present": True,
                "plugin_present": True,
                "data_file_count": 1,
                "data_bytes": 10,
                "data_files": [{"path": "/private/user/.claude-mem/private.db", "bytes": 10}],
            },
            claude_project_memory={
                "memory_file_count": 1,
                "memory_est_tokens": 25,
                "memory_files": [
                    {
                        "path": "/private/user/.claude/projects/private/memory/MEMORY.md",
                        "est_tokens": 25,
                    }
                ],
            },
            static={
                "always_on_files": [
                    {"path": "/private/user/.codex/AGENTS.md", "est_tokens": 12}
                ],
            },
            plugins={
                "available": True,
                "plugins": [
                    {"name": "private-plugin-name", "version": "1.0.0", "scope": "user"}
                ],
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.md"
            write_markdown(path, audit, rows=[])
            text = path.read_text()

        self.assertIn("Redacted by default", text)
        self.assertNotIn("/private/user", text)
        self.assertNotIn("private-plugin-name", text)
        self.assertIn("private runtime components", text)


if __name__ == "__main__":
    unittest.main()
