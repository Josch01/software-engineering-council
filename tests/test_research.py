import tempfile
import unittest
from pathlib import Path

from sec_council.contracts import CasePacket
from sec_council.literature import (cited_references, doi_metadata, download_pdf,
                                    search_openalex)
from sec_council.sandbox import run_python_docker
from sec_council.scientific_bridge import handoff, inspect_skill


class ResearchTests(unittest.TestCase):
    def test_research_is_explicit(self):
        with self.assertRaises(PermissionError):
            search_openalex("ACOR")
        with self.assertRaises(PermissionError):
            doi_metadata("10.1000/test")
        with self.assertRaises(PermissionError):
            cited_references("https://openalex.org/W123")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(PermissionError):
                download_pdf("https://arxiv.org/pdf/1706.03762", Path(directory) / "a.pdf")

    def test_scientific_bridge_never_claims_invocation(self):
        with tempfile.TemporaryDirectory() as directory:
            check = inspect_skill(Path(directory))
            self.assertEqual(check.status, "BLOCKED")
            packet = CasePacket("prove uniqueness", "hypothesis", (), (), (), "question")
            self.assertEqual(handoff(packet, Path(directory))["status"], "BLOCKED")

    def test_unapproved_sandbox_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "test.py").write_text("print('test')\n")
            result = run_python_docker(root, "test.py", root / "logs", approved=False)
            self.assertEqual(result.status.value, "BLOCKED")
            self.assertFalse((root / "logs").exists())


if __name__ == "__main__":
    unittest.main()
