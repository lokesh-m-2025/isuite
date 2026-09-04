"""Logging configuration for the ETL pipeline.

Provides structured logging to CloudWatch Logs and console.
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
import boto3
from src.config import config


class CloudWatchHandler(logging.Handler):
    """Custom logging handler that sends logs to AWS CloudWatch."""

    def __init__(self, log_group: str, log_stream: str):
        """Initialize CloudWatch handler.

        Args:
            log_group: CloudWatch Log Group name
            log_stream: CloudWatch Log Stream name
        """
        super().__init__()
        self.log_group = log_group
        self.log_stream = log_stream
        self.logs_client = boto3.client("logs", region_name=config.aws_region)

        # Create log group and stream if they don't exist
        self._ensure_log_stream()

    def _ensure_log_stream(self) -> None:
        """Ensure log group and stream exist."""
        try:
            self.logs_client.create_log_group(logGroupName=self.log_group)
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            pass

        try:
            self.logs_client.create_log_stream(
                logGroupName=self.log_group, logStreamName=self.log_stream
            )
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            pass

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to CloudWatch.

        Args:
            record: LogRecord to emit
        """
        try:
            message = self.format(record)
            timestamp = int(record.created * 1000)

            self.logs_client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[
                    {
                        "timestamp": timestamp,
                        "message": message,
                    }
                ],
            )
        except Exception as e:
            # Fallback to stderr if CloudWatch write fails
            self.handleError(record)


class StructuredFormatter(logging.Formatter):
    """Formatter that outputs structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON.

        Args:
            record: LogRecord to format

        Returns:
            JSON-formatted log message
        """
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "metrics"):
            log_obj["metrics"] = record.metrics

        return json.dumps(log_obj)


def setup_logger(name: str) -> logging.Logger:
    """Set up and return a configured logger.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Clear any existing handlers
    logger.handlers.clear()

    # Console handler with structured formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = StructuredFormatter()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # CloudWatch handler
    try:
        cloudwatch_handler = CloudWatchHandler(
            config.log_group_name, config.log_stream_name
        )
        cloudwatch_handler.setLevel(logging.INFO)
        cloudwatch_handler.setFormatter(console_formatter)
        logger.addHandler(cloudwatch_handler)
    except Exception as e:
        logger.warning(f"Failed to initialize CloudWatch logging: {e}")

    return logger


def log_metrics(
    logger: logging.Logger,
    level: int,
    message: str,
    metrics: Optional[Dict[str, Any]] = None,
) -> None:
    """Log a message with structured metrics.

    Args:
        logger: Logger instance
        level: Log level (e.g., logging.INFO)
        message: Log message
        metrics: Dictionary of metrics to include in log
    """
    record = logging.LogRecord(
        name=logger.name,
        level=level,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    record.metrics = metrics or {}
    logger.handle(record)
