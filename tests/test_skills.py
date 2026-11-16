import json
import tempfile
import unittest
from pathlib import Path

from sec_council.memory import new_project
from sec_council.skills import activate_skill, load_skill, read_resource


SKILL = (
    "---\nname: optimizer-rag\ndescription: Optimización y ciencia de datos\n"
    "version: 1.0.0\n---\n\n# Rules\nSelect dynamic roles.\n"
)


class SkillTests(unittest.TestCase):
    def test_local_activation_never_claims_spawn(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            skill_dir = root / "skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(SKILL, encoding="utf-8")
            (skill_dir / "agents").mkdir()
            (skill_dir / "agents/ROUTER.md").write_text("Dynamic roles")
            project = new_project(root / "projects", "case1", "Optimize")
            skill = load_skill(str(skill_dir))
            self.assertEqual(read_resource(skill, "agents/ROUTER.md")["text"], "Dynamic roles")
            result = activate_skill(skill=skill, goal="Optimizar", project=project)
            self.assertEqual(result["mode"], "SEQUENTIAL_ROLE_PASSES")
            session = json.loads((project / "skill_session/SESSION.json").read_text())
            self.assertEqual(session["role_selection"], "DYNAMIC_BY_ACTIVATED_SKILL")
            self.assertFalse(session["agent_runtime_invoked"])
            self.assertEqual(session["selected_roles"], [])

    def test_native_mode_is_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "SKILL.md").write_text(SKILL)
            project = new_project(p / "projects", "case1", "Optimize")
            result = activate_skill(skill=load_skill(str(p)), goal="Optimize",
                                    project=project, supports_native_subagents=True)
            self.assertEqual(result["mode"], "NATIVE_SUBAGENTS")
            self.assertFalse(result["agent_runtime_invoked"])

    def test_registry_and_bad_paths(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            directory = p / "my_skill"
            directory.mkdir()
            (directory / "SKILL.md").write_text(SKILL)
            registry = p / "registry.json"
            registry.write_text(json.dumps({"X": {"source": "my_skill"}}))
            skill = load_skill("X", registry_path=registry)
            self.assertEqual(skill.name, "optimizer-rag")
            with self.assertRaises(ValueError):
                read_resource(skill, "../secret.txt")
            with self.assertRaises(PermissionError):
                load_skill("https://github.com/Someone/Repo")
            with self.assertRaises(ValueError):
                load_skill("https://evil.example/skill")
            (directory / "SKILL.md").write_text("not a skill")
            with self.assertRaises(ValueError):
                load_skill(str(directory))

    def test_skill_is_not_executed(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "SKILL.md").write_text(SKILL + "\n!touch GOT_EXECUTED\n")
            self.assertIn("!touch", load_skill(str(p)).text)
            self.assertFalse((p / "GOT_EXECUTED").exists())


if __name__ == "__main__":
    unittest.main()
