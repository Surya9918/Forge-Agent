import unittest
from forgeagent.config.models import ForgeConfig, AutonomyMode
from forgeagent.config.loader import load_config


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = ForgeConfig()
        self.assertEqual(cfg.agent.mode, AutonomyMode.AUTONOMOUS)
        self.assertEqual(cfg.agent.max_iterations, 10)
        self.assertTrue(cfg.git.auto_commit)
        self.assertTrue(cfg.is_action_permitted("write_file"))
        self.assertFalse(cfg.is_action_permitted("force_push"))

    def test_assisted_mode(self):
        cfg = ForgeConfig(agent={"mode": AutonomyMode.ASSISTED})
        self.assertFalse(cfg.is_action_permitted("git_commit"))

    def test_safe_production_mode(self):
        cfg = ForgeConfig(agent={"mode": AutonomyMode.SAFE_PRODUCTION})
        self.assertTrue(cfg.is_action_permitted("write_file"))
        self.assertFalse(cfg.is_action_permitted("force_push"))
        self.assertFalse(cfg.is_action_permitted("repository_delete"))

    def test_loader_overrides(self):
        cfg = load_config(overrides={"project": {"name": "custom-app"}})
        self.assertEqual(cfg.project.name, "custom-app")


if __name__ == "__main__":
    unittest.main()
