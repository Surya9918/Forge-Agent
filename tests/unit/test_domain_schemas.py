import unittest
from forgeagent.domain.models import (
    PlanTask,
    DevelopmentPlan,
    CodeAction,
    TaskImplementation,
    RepairPatch,
)
from forgeagent.compat import model_to_dict, model_from_dict


class TestDomainSchemas(unittest.TestCase):
    def test_task_implementation_defaults(self):
        impl = TaskImplementation(task_id="t-101")
        self.assertEqual(impl.task_id, "t-101")
        self.assertIsInstance(impl.actions, list)
        self.assertEqual(len(impl.actions), 0)
        self.assertEqual(impl.status, "completed")

    def test_code_action_schema(self):
        action = CodeAction(
            file_path="src/main.py",
            action="write",
            content="print('hello')",
            explanation="Main entry point"
        )
        self.assertEqual(action.file_path, "src/main.py")
        self.assertEqual(action.action, "write")
        self.assertEqual(action.content, "print('hello')")

        # Test round-trip serialization
        d = model_to_dict(action)
        restored = model_from_dict(CodeAction, d)
        self.assertEqual(restored.file_path, action.file_path)

    def test_repair_patch_canonical_contract(self):
        patch = RepairPatch(
            file_path="calculator.py",
            operation="replace",
            fixed_content="def add(a, b): return a + b\n",
            explanation="Fixed subtraction to addition",
            confidence=0.98
        )
        self.assertEqual(patch.file_path, "calculator.py")
        self.assertEqual(patch.operation, "replace")
        self.assertTrue(patch.is_valid)
        self.assertEqual(patch.confidence, 0.98)

    def test_invalid_repair_patch(self):
        patch = RepairPatch(file_path="", fixed_content="")
        self.assertFalse(patch.is_valid)

    def test_development_plan_contract(self):
        plan = DevelopmentPlan(
            project="test-proj",
            description="Testing plan",
            stack={"backend": "python"},
            tasks=[PlanTask(id="1", title="Init", description="Initial task")],
            acceptance_criteria=["Tests pass"]
        )
        self.assertEqual(plan.project, "test-proj")
        self.assertEqual(len(plan.tasks), 1)
        self.assertEqual(plan.tasks[0].id, "1")


if __name__ == "__main__":
    unittest.main()
