import logging
import sys
from typing import Optional


def setup_logger(
    log_file_path: str,
    cloudwatch_enabled: bool = False,
    cloudwatch_group: Optional[str] = None,
    cloudwatch_stream: Optional[str] = None,
) -> logging.Logger:
    """Configure and return a logger for the ETL pipeline.
    
    Args:
        log_file_path: Path to local log file
        cloudwatch_enabled: Whether to send logs to CloudWatch
        cloudwatch_group: CloudWatch log group name (if enabled)
        cloudwatch_stream: CloudWatch log stream name (if enabled)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("etl_pipeline")
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Format: timestamp | level | logger_name | message
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # File handler
    try:
        file_handler = logging.FileHandler(log_file_path, mode="a")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create file handler: {e}", file=sys.stderr)
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # CloudWatch handler (optional)
    if cloudwatch_enabled:
        try:
            import watchtower
            
            cloudwatch_handler = watchtower.CloudWatchLogHandler(
                log_group=cloudwatch_group or "etl_pipeline",
                stream_name=cloudwatch_stream or "orders_etl",
            )
            cloudwatch_handler.setLevel(logging.INFO)
            cloudwatch_handler.setFormatter(formatter)
            logger.addHandler(cloudwatch_handler)
        except ImportError:
            logger.warning(
                "watchtower not available; CloudWatch logging disabled. "
                "Install with: pip install watchtower"
            )
        except Exception as e:
            logger.warning(f"Could not initialize CloudWatch logging: {e}")
    
    return logger
