import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.claude_mem_ab_benchmark import benchmark, estimate_tokens, real_db_counts, write_markdown


class ClaudeMemAbBenchmarkTest(unittest.TestCase):
    def test_benchmark_saves_tokens_without_losing_relevant_records(self):
        result = benchmark(total=60, relevant=6, search_limit=20, fetch_count=6)

        self.assertTrue(result["accepted"])
        self.assertEqual(result["relevant_found_in_fetch"], 6)
        self.assertGreater(result["baseline_fetch_all_tokens"], result["search_filter_fetch_tokens"])
        self.assertGreater(result["saved_tokens"], 0)
        self.assertGreater(result["reduction_pct"], 50)

    def test_estimate_tokens_uses_chars_div_four(self):
        self.assertEqual(estimate_tokens("x" * 40), 10)

    def test_real_db_counts_returns_zero_for_missing_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            counts = real_db_counts(Path(tmp) / "missing.db")

        self.assertEqual(
            counts,
            {
                "sdk_sessions": 0,
                "user_prompts": 0,
                "observations": 0,
                "session_summaries": 0,
            },
        )

    def test_markdown_uses_redacted_database_label(self):
        result = benchmark(total=10, relevant=2, search_limit=5, fetch_count=2)
        counts = {
            "sdk_sessions": 0,
            "user_prompts": 0,
            "observations": 0,
            "session_summaries": 0,
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "claude-mem.md"
            write_markdown(path, result, counts, "redacted memory database")
            text = path.read_text()

        self.assertIn("redacted memory database", text)
        self.assertNotIn("/private/user", text)
        self.assertNotIn("claude-mem.db", text)


if __name__ == "__main__":
    unittest.main()
