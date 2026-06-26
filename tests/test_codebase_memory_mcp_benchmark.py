import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.codebase_memory_mcp_benchmark import (
    build_benchmark,
    estimate_tokens_from_bytes,
    graph_stats,
    reduction_pct,
    write_markdown,
)


class CodebaseMemoryMcpBenchmarkTest(unittest.TestCase):
    def test_token_estimate_and_reduction(self):
        self.assertEqual(estimate_tokens_from_bytes(400), 100)
        self.assertEqual(reduction_pct(100, 25), 75.0)
        self.assertEqual(reduction_pct(0, 25), 0.0)

    def test_graph_stats_reads_codebase_memory_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "project.db"
            db = sqlite3.connect(db_path)
            db.execute("CREATE TABLE file_hashes (project TEXT, rel_path TEXT, size INTEGER)")
            db.execute("CREATE TABLE nodes (project TEXT)")
            db.execute("CREATE TABLE edges (project TEXT)")
            db.executemany(
                "INSERT INTO file_hashes VALUES ('p', ?, ?)",
                [("a.kt", 100), ("b.kt", 300)],
            )
            db.executemany("INSERT INTO nodes VALUES ('p')", [(), (), ()])
            db.executemany("INSERT INTO edges VALUES ('p')", [(), ()])
            db.commit()
            db.close()

            stats = graph_stats(db_path, "p")

        self.assertEqual(stats.indexed_files, 2)
        self.assertEqual(stats.indexed_source_bytes, 400)
        self.assertEqual(stats.nodes, 3)
        self.assertEqual(stats.edges, 2)
        self.assertGreater(stats.db_bytes, 0)

    def test_build_benchmark_compares_outputs_to_indexed_matching_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            (repo / "a.kt").write_text("ExampleWorker\n" + ("x" * 399))
            (repo / "b.kt").write_text("unrelated\n" + ("y" * 199))
            (repo / "app").mkdir()
            (repo / "app" / "src").mkdir(parents=True, exist_ok=True)

            db_path = root / "project.db"
            db = sqlite3.connect(db_path)
            db.execute("CREATE TABLE file_hashes (project TEXT, rel_path TEXT, size INTEGER)")
            db.execute("CREATE TABLE nodes (project TEXT)")
            db.execute("CREATE TABLE edges (project TEXT)")
            project = "private-project-key"
            db.executemany(
                "INSERT INTO file_hashes VALUES ('p', ?, ?)",
                [("a.kt", 416), ("b.kt", 209)],
            )
            db.execute("UPDATE file_hashes SET project = ?", (project,))
            db.execute("INSERT INTO nodes VALUES (?)", (project,))
            db.execute("INSERT INTO edges VALUES (?)", (project,))
            db.commit()
            db.close()

            output_paths = []
            for name in ["search", "query", "trace", "arch", "code"]:
                path = root / f"{name}.json"
                path.write_text("{}")
                output_paths.append(path)
            time_path = root / "time.txt"
            time_path.write_text("elapsed_seconds=1.5 max_rss_kb=12345\n")

            result = build_benchmark(
                repo_path=repo,
                db_path=db_path,
                project=project,
                domain_pattern="ExampleWorker",
                trace_files=["a.kt"],
                time_path=time_path,
                search_graph_path=output_paths[0],
                query_graph_path=output_paths[1],
                trace_path=output_paths[2],
                architecture_path=output_paths[3],
                search_code_path=output_paths[4],
            )

        self.assertEqual(result["domain_file_count"], 1)
        self.assertGreater(result["domain_file_bytes"], 0)
        self.assertEqual(result["time"]["index_elapsed_seconds"], 1.5)
        self.assertEqual(result["time"]["index_max_rss_kb"], 12345)
        self.assertEqual(len(result["scenarios"]), 5)

        with tempfile.TemporaryDirectory() as tmp:
            markdown_path = Path(tmp) / "benchmark.md"
            write_markdown(markdown_path, result)
            text = markdown_path.read_text()

        self.assertIn("redacted repository", text)
        self.assertIn("redacted project", text)
        self.assertIn("redacted index database", text)
        self.assertNotIn(str(repo), text)
        self.assertNotIn(str(db_path), text)
        self.assertNotIn(project, text)


if __name__ == "__main__":
    unittest.main()
