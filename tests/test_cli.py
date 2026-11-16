import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from sec_council.cli import main


class CliTests(unittest.TestCase):
    def call(self, args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(args)
        return code, json.loads(buf.getvalue())

    def test_route(self):
        code, result = self.call(["route", "Auditar mi script ACOR", "--source", "solver.py"])
        self.assertEqual(code, 0)
        self.assertEqual(result["kind"], "CODE_AUDIT")

    def test_local_skill_cli_and_workflow(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            skill = base / "skills" / "sample"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: example-skill\ndescription: Demo skill\n"
                "version: 1.0\n---\n# Demo\n", encoding="utf-8")
            code = base / "code"
            code.mkdir()
            (code / "demo.py").write_text("def objective(x):\n    return x*x\n")
            rc, result = self.call([
                "analyze", "case1", "--goal", "Analizar mi código",
                "--workspace", str(base / "projects"),
                "--source", str(code), "--skill", str(skill)])
            self.assertEqual(rc, 0)
            self.assertEqual(result["skill_session"]["skill"]["name"], "example-skill")
            self.assertFalse(result["skill_session"]["agent_runtime_invoked"])
            rc2, inspected = self.call(["skill", "inspect", str(skill)])
            self.assertEqual(rc2, 0)
            self.assertEqual(inspected["skill"]["name"], "example-skill")

    def test_project_init(self):
        with tempfile.TemporaryDirectory() as directory:
            code, result = self.call(["init", "case1", "--goal", "audit",
                                      "--workspace", directory])
            self.assertEqual(code, 0)
            self.assertTrue(Path(result["path"]).exists())


if __name__ == "__main__":
    unittest.main()
