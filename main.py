import logging
import sys
from src.etl_pipeline import CustomerTotalsETL

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def main():
    setup_logging()
    logger = logging.getLogger("main")
    try:
        pipeline = CustomerTotalsETL()
        pipeline.run()
    except Exception as e:
        logger.critical("ETL execution failed: %s", e, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
