import sys
import logging
from src.config import PipelineConfig
from src.pipeline import run_pipeline


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("main")

    try:
        config = PipelineConfig()
        logger.info(f"Running pipeline: {config.source_s3_path} -> {config.target_s3_path}")
        metrics = run_pipeline(config)
        print(f"Pipeline completed successfully: {metrics}")
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
