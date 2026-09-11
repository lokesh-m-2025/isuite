import unittest
import os
from config import Config


class TestConfig(unittest.TestCase):
    """Tests for Config class."""

    def test_from_environment_success(self):
        """Valid environment variables should load config."""
        os.environ["SOURCE_BUCKET"] = "test-source"
        os.environ["SOURCE_KEY"] = "input/test.csv"
        os.environ["TARGET_BUCKET"] = "test-target"
        os.environ["TARGET_KEY"] = "output/test.csv"
        
        config = Config.from_environment()
        
        self.assertEqual(config.source_bucket, "test-source")
        self.assertEqual(config.source_key, "input/test.csv")
        self.assertEqual(config.target_bucket, "test-target")
        self.assertEqual(config.target_key, "output/test.csv")
        
        # Clean up
        for key in ["SOURCE_BUCKET", "SOURCE_KEY", "TARGET_BUCKET", "TARGET_KEY"]:
            os.environ.pop(key, None)

    def test_from_environment_missing_required(self):
        """Missing required environment variables should raise ValueError."""
        os.environ.pop("SOURCE_BUCKET", None)
        os.environ.pop("SOURCE_KEY", None)
        os.environ.pop("TARGET_BUCKET", None)
        os.environ.pop("TARGET_KEY", None)
        
        with self.assertRaises(ValueError) as context:
            Config.from_environment()
        
        self.assertIn("SOURCE_BUCKET", str(context.exception))

    def test_config_defaults(self):
        """Config should have sensible defaults."""
        config = Config(
            source_bucket="test-source",
            source_key="input/test.csv",
            target_bucket="test-target",
            target_key="output/test.csv",
        )
        
        self.assertEqual(config.aws_region, "us-east-1")
        self.assertEqual(config.log_file_path, "etl_pipeline.log")
        self.assertIn("customer_id", config.required_columns)
        self.assertIn("amount", config.required_columns)


if __name__ == "__main__":
    unittest.main()
