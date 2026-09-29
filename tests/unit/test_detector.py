import unittest
import tempfile
from pathlib import Path
from forgeagent.intelligence.detector import ProjectDetector


class TestDetector(unittest.TestCase):
    def test_detect_python(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "requirements.txt").write_text("pydantic\n")
            info = ProjectDetector.detect(Path(tmpdir))
            self.assertEqual(info.primary_language, "python")
            self.assertEqual(info.package_manager, "pip")
            self.assertIn("unittest", info.test_command)

    def test_detect_node(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "package.json").write_text('{"name": "test"}')
            info = ProjectDetector.detect(Path(tmpdir))
            self.assertEqual(info.primary_language, "javascript")
            self.assertEqual(info.package_manager, "npm")
            self.assertEqual(info.test_command, "npm test")

    def test_detect_rust(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "Cargo.toml").write_text('[package]\nname = "test"')
            info = ProjectDetector.detect(Path(tmpdir))
            self.assertEqual(info.primary_language, "rust")
            self.assertEqual(info.package_manager, "cargo")


if __name__ == "__main__":
    unittest.main()
