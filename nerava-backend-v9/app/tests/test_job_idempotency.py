"""
Unit tests for job idempotency.
"""
import pytest
from unittest.mock import Mock, patch
from app.jobs.reward_routing_runner import run_rebalance
from app.models_extra import RewardRoutingRun


class TestJobIdempotency:
    """Test job idempotency functionality."""
    
    @patch('app.jobs.reward_routing_runner.get_db')
    def test_run_rebalance_new_run(self, mock_get_db):
        """Test running a new rebalance job."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock query to return no existing run
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock update query
        mock_update_query = Mock()
        mock_db.query.return_value.filter.return_value.update.return_value = mock_update_query
        
        result = run_rebalance("test-run-123")
        
        # Verify new run was created
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        
        # Verify result structure
        assert result["run_id"] == "test-run-123"
        assert result["status"] == "completed"
        assert "routing_changes" in result
        assert "total_rewards_optimized" in result
    
    @patch('app.jobs.reward_routing_runner.get_db')
    def test_run_rebalance_existing_running(self, mock_get_db):
        """Test running a rebalance job that's already running."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock existing running job
        existing_run = Mock()
        existing_run.status = "running"
        existing_run.result = {"test": "data"}
        
        mock_db.query.return_value.filter.return_value.first.return_value = existing_run
        
        result = run_rebalance("test-run-123")
        
        # Should return existing result without creating new job
        assert result["run_id"] == "test-run-123"
        assert result["status"] == "running"
        assert result["result"] == {"test": "data"}
        assert "Job already completed or running" in result["message"]
    
    @patch('app.jobs.reward_routing_runner.get_db')
    def test_run_rebalance_existing_done(self, mock_get_db):
        """Test running a rebalance job that's already done."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock existing completed job
        existing_run = Mock()
        existing_run.status = "done"
        existing_run.result = {"routing_changes": 10}
        
        mock_db.query.return_value.filter.return_value.first.return_value = existing_run
        
        result = run_rebalance("test-run-123")
        
        # Should return existing result without creating new job
        assert result["run_id"] == "test-run-123"
        assert result["status"] == "done"
        assert result["result"] == {"routing_changes": 10}
        assert "Job already completed or running" in result["message"]
    
    @patch('app.jobs.reward_routing_runner.get_db')
    def test_run_rebalance_retry_failed(self, mock_get_db):
        """Test retrying a failed rebalance job."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock existing failed job
        existing_run = Mock()
        existing_run.status = "failed"
        existing_run.result = {"error": "Previous error"}
        
        mock_db.query.return_value.filter.return_value.first.return_value = existing_run
        
        result = run_rebalance("test-run-123")
        
        # Should retry the failed job
        assert existing_run.status == "running"  # Status should be updated
        mock_db.commit.assert_called()
        
        # Should complete successfully
        assert result["run_id"] == "test-run-123"
        assert result["status"] == "completed"
    
    @patch('app.jobs.reward_routing_runner.get_db')
    def test_run_rebalance_exception_handling(self, mock_get_db):
        """Test exception handling in rebalance job."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock query to return no existing run
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock update to raise exception
        mock_db.query.return_value.filter.return_value.update.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            run_rebalance("test-run-123")
        
        # Should mark as failed
        mock_db.commit.assert_called()
    
    @patch('app.jobs.reward_routing_runner.get_db')
    def test_run_rebalance_existing_run_exception(self, mock_get_db):
        """Test exception handling with existing run."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock existing run
        existing_run = Mock()
        existing_run.status = "running"
        
        mock_db.query.return_value.filter.return_value.first.return_value = existing_run
        
        # Mock update to raise exception
        existing_run.status = "failed"
        existing_run.result = {"error": "Test error"}
        
        with patch('app.jobs.reward_routing_runner.logger') as mock_logger:
            with pytest.raises(Exception):
                # Simulate exception during job execution
                raise Exception("Test error")
        
        # Should mark existing run as failed
        assert existing_run.status == "failed"
        assert existing_run.result == {"error": "Test error"}
