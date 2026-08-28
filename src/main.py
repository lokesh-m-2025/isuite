import sys
import logging
from src.config import Config
from src.etl import run_pipeline

if __name__ == "__main__":
    try:
        cfg = Config.load()
        run_pipeline(cfg)
    except Exception as e:
        logging.getLogger(__name__).critical(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)
