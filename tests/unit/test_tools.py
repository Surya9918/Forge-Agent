import unittest
import tempfile
from pathlib import Path
from forgeagent.tools.registry import ToolRegistry
from forgeagent.config.models import ForgeConfig


class TestTools(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.workspace = self.tmpdir.name
        self.registry = ToolRegistry(workspace_root=self.workspace)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_write_and_read_file(self):
        res_write = self.registry.execute_tool("write_file", file_path="hello.txt", content="Hello Antigravity")
        self.assertTrue(res_write.success)

        res_read = self.registry.execute_tool("read_file", file_path="hello.txt")
        self.assertTrue(res_read.success)
        self.assertEqual(res_read.data, "Hello Antigravity")

    def test_path_traversal_blocked(self):
        res = self.registry.execute_tool("read_file", file_path="../../../etc/passwd")
        self.assertFalse(res.success)
        self.assertIn("Access violation", res.error)

    def test_edit_file(self):
        self.registry.execute_tool("write_file", file_path="calc.py", content="def add(a, b): return a - b\n")
        res_edit = self.registry.execute_tool("edit_file", file_path="calc.py", old_content="return a - b", new_content="return a + b")
        self.assertTrue(res_edit.success)

        read_res = self.registry.execute_tool("read_file", file_path="calc.py")
        self.assertIn("return a + b", read_res.data)

    def test_denied_command(self):
        res = self.registry.execute_tool("run_command", command="rm -rf /")
        self.assertFalse(res.success)
        self.assertIn("Security Policy Violation", res.error)


if __name__ == "__main__":
    unittest.main()
