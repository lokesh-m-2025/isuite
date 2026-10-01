"""Tests for pipeline orchestration."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from src.pipeline import _initialize_schema, _is_already_processed, _record_execution


class TestPipelineExecutionTracking:
    """Tests for execution tracking and idempotency."""

    def test_is_already_processed_true(self):
        """Test detection of already processed date."""
        mock_conn = MagicMock()
        mock_conn.fetch_one.return_value = (1,)

        result = _is_already_processed(mock_conn, date(2024, 1, 15))

        assert result is True
        mock_conn.fetch_one.assert_called_once()

    def test_is_already_processed_false(self):
        """Test detection of new date."""
        mock_conn = MagicMock()
        mock_conn.fetch_one.return_value = (0,)

        result = _is_already_processed(mock_conn, date(2024, 1, 15))

        assert result is False

    def test_record_execution_success(self):
        """Test successful execution recording."""
        mock_conn = MagicMock()

        _record_execution(
            mock_conn,
            date(2024, 1, 15),
            "SUCCESS",
            processed_count=10,
            successful_count=10,
            rejected_count=0,
        )

        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0][0]
        assert "SUCCESS" in call_args
        assert "2024-01-15" in call_args

    def test_initialize_schema(self):
        """Test schema initialization."""
        mock_conn = MagicMock()

        _initialize_schema(mock_conn)

        # Should call execute 4 times (4 CREATE TABLE statements)
        assert mock_conn.execute.call_count == 4
        calls = [call[0][0] for call in mock_conn.execute.call_args_list]
        assert any("ORDERS_STAGING" in call for call in calls)
        assert any("ORDERS" in call for call in calls)
        assert any("REJECTED_RECORDS" in call for call in calls)
        assert any("PIPELINE_EXECUTION_LOG" in call for call in calls)
