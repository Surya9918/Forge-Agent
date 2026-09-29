import unittest
import tempfile
from forgeagent.antigravity.mcp_server import ForgeMCPServer


class TestMCPServer(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.server = ForgeMCPServer(workspace_root=self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_initialize(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        resp = self.server.handle_request(req)
        self.assertEqual(resp["id"], 1)
        self.assertEqual(resp["result"]["serverInfo"]["name"], "ForgeAgent")
        self.assertIn("tools", resp["result"]["capabilities"])

    def test_tools_list(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        resp = self.server.handle_request(req)
        tool_names = [t["name"] for t in resp["result"]["tools"]]
        self.assertIn("forge_plan", tool_names)
        self.assertIn("forge_develop", tool_names)
        self.assertIn("forge_test_and_heal", tool_names)
        self.assertIn("forge_status", tool_names)

    def test_tools_call_plan(self):
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "forge_plan",
                "arguments": {"requirement": "Build a simple calculator"}
            }
        }
        resp = self.server.handle_request(req)
        self.assertEqual(resp["id"], 3)
        self.assertTrue(len(resp["result"]["content"]) > 0)


if __name__ == "__main__":
    unittest.main()
