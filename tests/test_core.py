import json
import tempfile
import unittest
from pathlib import Path

from sec_council.budgets import BudgetExceeded, ResourceBudget
from sec_council.contracts import (CasePacket, CheckResult, Decision, EvidenceCard,
                                    EpistemicType, GateStatus, TaskRequest)
from sec_council.gates import technical_gate
from sec_council.graph import Edge, EvidenceGraph, Node
from sec_council.memory import new_project, record
from sec_council.permissions import authorize, inside
from sec_council.router import route
from sec_council.workflow import Phase, Workflow


class CoreTests(unittest.TestCase):
    def test_routing_acor_code_to_minimal_specialists(self):
        result = route(TaskRequest("Auditar implementación ACOR", ("optimizer.py",)))
        self.assertEqual(result.kind.value, "CODE_AUDIT")
        self.assertIn("optimization-expert", result.workers)
        self.assertEqual(result.reviewer, "adversarial-auditor")
        self.assertLessEqual(len(result.all_agents), 4)

    def test_theory_escalates(self):
        result = route(TaskRequest("Demuestra un teorema de álgebra diferencial"))
        self.assertTrue(result.scientific_escalation)

    def test_budget_fails_closed(self):
        with self.assertRaises(BudgetExceeded):
            ResourceBudget(max_files_scanned=1).enforce("files", 2)
        with self.assertRaises(ValueError):
            ResourceBudget(max_agents=9)

    def test_role_locks_and_paths(self):
        authorize("python-engineer", "write_patch")
        with self.assertRaises(PermissionError):
            authorize("python-engineer", "certify_scientific_claim")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(inside(root, "reports/a.json"), root / "reports/a.json")
            with self.assertRaises(PermissionError):
                inside(root, "../outside.txt")

    def test_decision_needs_evidence(self):
        with self.assertRaises(ValueError):
            Decision("D1", "Rewrite algorithm", "faster", (), status="ACCEPTED")
        with self.assertRaises(ValueError):
            EvidenceCard("E1", "Title", "url", "p.1", "claim", (),
                         EpistemicType.LITERATURE, verified=True)

    def test_project_state_and_immutable_record(self):
        with tempfile.TemporaryDirectory() as directory:
            project = new_project(Path(directory), "case-1", "Review ACOR")
            self.assertTrue((project / "MEMORY_CORE.md").exists())
            check = CheckResult("syntax", GateStatus.PASS, "parsed")
            path = record(project, "checks", "CHK-1", check)
            self.assertEqual(json.loads(path.read_text())["status"], "PASS")
            with self.assertRaises(FileExistsError):
                record(project, "checks", "CHK-1", check)
            with self.assertRaises(ValueError):
                new_project(Path(directory), "../escape", "bad")

    def test_workflow_and_review(self):
        wf = Workflow()
        wf.advance(Phase.SCOPED)
        wf.advance(Phase.REVIEWED)
        with self.assertRaises(PermissionError):
            wf.advance(Phase.TESTED)
        check = CheckResult("unit", GateStatus.PASS, "pytest")
        wf.advance(Phase.TESTED, checks=(check,))
        wf.advance(Phase.AUDITED)
        with self.assertRaises(PermissionError):
            wf.advance(Phase.RELEASED, checks=(check,))
        wf.advance(Phase.RELEASED, checks=(check,), independently_reviewed=True)
        self.assertEqual(wf.phase, Phase.RELEASED)
        self.assertEqual(technical_gate((check,), author="a", independent_reviewer="a")["status"],
                         "BLOCKED")
        self.assertEqual(technical_gate((check,), author="a", independent_reviewer="b")["status"],
                         "PASS")

    def test_graph_references(self):
        graph = EvidenceGraph()
        graph.add_node(Node("C", "CLAIM", "Tested claim"))
        with self.assertRaises(ValueError):
            graph.add_edge(Edge("C", "missing", "SUPPORTED_BY"))
        graph.add_node(Node("P", "PAPER", "Reference"))
        graph.add_edge(Edge("C", "P", "SUPPORTED_BY"))
        self.assertEqual(len(graph.to_dict()["edges"]), 1)


if __name__ == "__main__":
    unittest.main()
