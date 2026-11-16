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

    def test_project_init(self):
        with tempfile.TemporaryDirectory() as directory:
            code, result = self.call(["init", "case1", "--goal", "audit",
                                      "--workspace", directory])
            self.assertEqual(code, 0)
            self.assertTrue(Path(result["path"]).exists())


if __name__ == "__main__":
    unittest.main()
