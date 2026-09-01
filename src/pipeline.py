import logging
import sys
from src.config import PipelineConfig
from src.extractor import S3Extractor
from src.transformer import OrderTransformer
from src.loader import S3Loader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("ETLPipeline")

def run_pipeline() -> None:
    logger.info("Initializing Order Aggregation Pipeline...")
    config = PipelineConfig()
    
    extractor = S3Extractor(config)
    transformer = OrderTransformer()
    loader = S3Loader(config)
    
    try:
        raw_df = extractor.extract_csv(config.source_s3_uri)
        transformed_df, metrics = transformer.transform(raw_df)
        loader.load_csv(transformed_df, config.target_s3_uri)
        logger.info(f"Pipeline execution finished successfully. Summary metrics: {metrics}")
    except Exception as e:
        logger.critical(f"Pipeline execution failed with exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()
