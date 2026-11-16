import json
import tempfile
import unittest
from pathlib import Path

from sec_council.conversation import (
    add_event, resume_conversation, start_conversation,
)
from sec_council.memory import new_project


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.project = new_project(self.root / "projects", "acortest", "Analizar ACOR")
        self.source = self.root / "solver.py"
        self.source.write_text("def objective(x):\n    return x*x\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_natural_start_does_not_authorize_edits(self):
        state = start_conversation(
            self.project, self.source, "Analiza este solver.py, trabajaremos con él")
        self.assertEqual(state["phase"], "UNDERSTAND_SOURCE")
        self.assertFalse(state["source_edit_authorized"])
        self.assertEqual(state["objective"], None)
        self.assertEqual(resume_conversation(self.project)["events_recorded"], 0)
        with self.assertRaises(FileExistsError):
            start_conversation(self.project, self.source, "Start again")

    def test_approval_gate_and_discussion_progress(self):
        start_conversation(self.project, self.source, "Audita el algoritmo")
        add_event(self.project, kind="FINDING", detail="Posible costo cuadrático",
                  evidence_refs=("solver.py:1-2",))
        add_event(self.project, kind="PROPOSAL", detail="Vectorizar el fitness",
                  proposal_id="P01")
        with self.assertRaises(PermissionError):
            add_event(self.project, kind="IMPLEMENTED", detail="Cambio realizado")
        with self.assertRaises(PermissionError):
            add_event(self.project, kind="USER_APPROVAL", detail="Sí",
                      actor="agent", proposal_id="P01", user_confirmed=True)
        state = add_event(self.project, kind="USER_APPROVAL", detail="Adelante con P01",
                          actor="user", proposal_id="P01", user_confirmed=True)
        self.assertTrue(state["source_edit_authorized"])
        state = add_event(self.project, kind="IMPLEMENTED",
                          detail="Se implementó P01 en un branch de prueba")
        self.assertEqual(state["phase"], "IMPLEMENTED_PENDING_TESTS")
        with self.assertRaises(PermissionError):
            add_event(self.project, kind="TEST_RESULT", detail="PASS", actor="agent")
        add_event(self.project, kind="TEST_RESULT",
                  detail="Conjunto local 7/7 ejecutado", actor="checker")
        add_event(self.project, kind="ADVERSARIAL_AUDIT",
                  detail="Revisor detectó dominio no cubierto", actor="reviewer")
        final = resume_conversation(self.project)
        self.assertEqual(final["technical_acceptance"], "NOT_PERFORMED")
        self.assertEqual(final["events_recorded"], 6)

    def test_objective_follows_user(self):
        start_conversation(self.project, self.source, "Analiza antes de cambiar")
        with self.assertRaises(PermissionError):
            add_event(self.project, kind="USER_OBJECTIVE", detail="Minimizar tiempo")
        state = add_event(self.project, kind="USER_OBJECTIVE", detail="Minimizar tiempo",
                          actor="user", user_confirmed=True)
        self.assertEqual(state["objective"], "Minimizar tiempo")
        self.assertFalse(state["source_edit_authorized"])
        plan = add_event(self.project, kind="PLAN", detail="Proponer plan de optimización")
        self.assertEqual(plan["phase"], "PLAN")
        # Planning is allowed after goal alignment; editing is still not authorized.
        self.assertFalse(plan["source_edit_authorized"])
        with self.assertRaises(PermissionError):
            add_event(self.project, kind="IMPLEMENTED", detail="Cambio sin permiso")
        self.assertEqual(resume_conversation(self.project)["status"], "IN_DISCUSSION")

    def test_no_claim_of_completed_audit_from_state(self):
        start_conversation(self.project, self.source, "Review")
        raw = json.loads((self.project / "CONVERSATION_STATE.json").read_text())
        self.assertEqual(raw["technical_acceptance"], "NOT_PERFORMED")
        self.assertEqual(raw["scientific_certification"], "NOT_PERFORMED")
        self.assertEqual(raw["events"], [])


if __name__ == "__main__":
    unittest.main()
