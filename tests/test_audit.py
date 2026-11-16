import tempfile
import unittest
from pathlib import Path

from sec_council.budgets import BudgetExceeded, ResourceBudget
from sec_council.static_audit import inventory


class AuditTests(unittest.TestCase):
    def test_ast_does_not_execute_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.py").write_text(
                "from pathlib import Path\n"
                "Path('DANGEROUS_SIDE_EFFECT').write_text('ran')\n"
                "def objective(x):\n    return x*x\n"
            )
            result = inventory(root)
            self.assertEqual(result["syntax_gate"], "PASS")
            self.assertEqual(result["scientific_correctness"], "NOT_ASSESSED")
            self.assertIn("objective", result["files"][0]["functions"])
            self.assertFalse((root / "DANGEROUS_SIDE_EFFECT").exists())

    def test_error_and_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bad.py").write_text("def f(:\n")
            self.assertEqual(inventory(root)["syntax_gate"], "FAIL")
            (root / "second.py").write_text("pass\n")
            with self.assertRaises(BudgetExceeded):
                inventory(root, ResourceBudget(max_files_scanned=1, max_file_bytes=1))


if __name__ == "__main__":
    unittest.main()
