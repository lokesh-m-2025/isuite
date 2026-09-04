"""Entry point for the ETL pipeline."""

import sys
from src.config import config
from src.logger import setup_logger
from src.pipeline import ETLPipeline

logger = setup_logger(__name__)


def main() -> int:
    """Execute the ETL pipeline.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Validate configuration
        config.validate()
        logger.info(f"Configuration validated. Region: {config.aws_region}")

        # Create and run pipeline
        pipeline = ETLPipeline()
        success = pipeline.run()

        if success:
            logger.info("Pipeline execution completed successfully")
            return 0
        else:
            logger.error("Pipeline execution failed")
            return 1

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
