import unittest
from forgeagent.observability.redactor import redact_secrets, redact_data


class TestRedactor(unittest.TestCase):
    def test_github_token_redaction(self):
        text = "My token is ghp_1234567890abcdefghijklmnopqrstuvwxyzAB"
        redacted = redact_secrets(text)
        self.assertNotIn("ghp_12345", redacted)
        self.assertIn("ghp_********", redacted)

    def test_openai_key_redaction(self):
        text = "Key sk-1234567890abcdefghijklmnopqrstuv"
        redacted = redact_secrets(text)
        self.assertIn("sk-********", redacted)

    def test_private_key_redaction(self):
        text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----"
        redacted = redact_secrets(text)
        self.assertIn("[REDACTED PRIVATE KEY]", redacted)

    def test_dict_redaction(self):
        data = {"auth": "Bearer secret_bearer_token_12345", "user": "alice"}
        redacted = redact_data(data)
        self.assertIn("Bearer ********", redacted["auth"])
        self.assertEqual(redacted["user"], "alice")


if __name__ == "__main__":
    unittest.main()
