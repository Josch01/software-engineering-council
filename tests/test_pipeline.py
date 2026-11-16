import json
import tempfile
import unittest
from pathlib import Path

from sec_council.budgets import ResourceBudget
from sec_council.config import load_budget
from sec_council.pipeline import analyze_project


class PipelineTests(unittest.TestCase):
    def test_offline_dossier_no_fabricated_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "code"
            source.mkdir()
            (source / "optimizer.py").write_text(
                "def objective(x):\n    return x*x\n", encoding="utf-8")
            result = analyze_project(
                workspace=base / "projects", project_name="acortest",
                goal="Audita optimización ACOR", source=source, online=False,
            )
            self.assertEqual(result["status"], "NEEDS_REVIEW")
            self.assertEqual(result["code_files_analyzed"], 1)
            report = json.loads(Path(result["report"]).read_text(encoding="utf-8"))
            self.assertEqual(report["executed_tests"], [])
            self.assertEqual(report["scientific_certification"], "NOT_PERFORMED")
            self.assertTrue(all(task["status"] == "NOT_RUN" for task in report["obligations"]))
            self.assertTrue((base / "projects/acortest/graphs/decision_graph.json").exists())

    def test_no_accidental_online_pdf_download(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(PermissionError):
                analyze_project(workspace=Path(directory), project_name="test",
                                goal="ACOR", online=False, download_pdfs=True)

    def test_toml_limit_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "config.toml"
            file.write_text("[council]\nmax_agents = 2\n[execution]\ntimeout_seconds = 60\n")
            budget = load_budget(file)
            self.assertEqual(budget.max_agents, 2)
            self.assertEqual(budget.timeout_seconds, 60)


if __name__ == "__main__":
    unittest.main()
