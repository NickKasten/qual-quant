import os
import unittest
from unittest.mock import patch
from config import load_config, get_public_config, ConfigError

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.env_vars = {
            "TIIINGO_API_KEY": "tiingo-key",
            "ALPHA_VANTAGE_API_KEY": "av-key",
            "ALPACA_API_KEY": "alpaca-key",
            "ALPACA_SECRET_KEY": "alpaca-secret",
            "SUPABASE_URL": "https://supabase.test",
            "SUPABASE_KEY": "supabase-key"
        }

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_env_vars_raises(self):
        with self.assertRaises(ConfigError) as ctx:
            load_config()
        self.assertIn("Missing required environment variables", str(ctx.exception))

    @patch.dict(os.environ, {
        "TIIINGO_API_KEY": "tiingo-key",
        "ALPHA_VANTAGE_API_KEY": "av-key",
        "ALPACA_API_KEY": "alpaca-key",
        "ALPACA_SECRET_KEY": "alpaca-secret",
        "SUPABASE_URL": "https://supabase.test",
        "SUPABASE_KEY": "supabase-key"
    }, clear=True)
    def test_load_config_success(self):
        cfg = load_config()
        self.assertEqual(cfg["TIIINGO_API_KEY"], "tiingo-key")
        self.assertEqual(cfg["SUPABASE_URL"], "https://supabase.test")
        self.assertIn("TIIINGO_BASE_URL", cfg)

    @patch.dict(os.environ, {
        "TIIINGO_API_KEY": "tiingo-key",
        "ALPHA_VANTAGE_API_KEY": "av-key",
        "ALPACA_API_KEY": "alpaca-key",
        "ALPACA_SECRET_KEY": "alpaca-secret",
        "SUPABASE_URL": "https://supabase.test",
        "SUPABASE_KEY": "supabase-key"
    }, clear=True)
    def test_get_public_config(self):
        public_cfg = get_public_config()
        self.assertIn("SUPABASE_URL", public_cfg)
        self.assertNotIn("SUPABASE_KEY", public_cfg)
        self.assertIn("TIIINGO_BASE_URL", public_cfg)

if __name__ == "__main__":
    unittest.main() 