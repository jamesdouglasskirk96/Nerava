"""
Background job for autonomous reward routing rebalance.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.dependencies import get_db
from app.models_extra import RewardRoutingRun
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

def run_rebalance(run_id: str) -> Dict[str, Any]:
    """
    Execute reward routing rebalance job with idempotency.
    
    Handles existing/running/done states to prevent duplicate execution.
    """
    
    logger.info(f"Starting reward routing rebalance", extra={
        "run_id": run_id,
        "job": "reward_routing_runner"
    })
    
    # Get database session
    db = next(get_db())
    
    try:
        # Check if run already exists
        existing_run = db.query(RewardRoutingRun).filter(
            RewardRoutingRun.run_id == run_id
        ).first()
        
        if existing_run:
            if existing_run.status in ["running", "done"]:
                logger.info(f"Reward routing rebalance already exists", extra={
                    "run_id": run_id,
                    "job": "reward_routing_runner",
                    "existing_status": existing_run.status
                })
                return {
                    "run_id": run_id,
                    "status": existing_run.status,
                    "result": existing_run.result,
                    "message": "Job already completed or running"
                }
            elif existing_run.status == "failed":
                # Retry failed job
                existing_run.status = "running"
                db.commit()
                logger.info(f"Retrying failed reward routing rebalance", extra={
                    "run_id": run_id,
                    "job": "reward_routing_runner"
                })
        else:
            # Create new run record
            new_run = RewardRoutingRun(
                run_id=run_id,
                status="running"
            )
            db.add(new_run)
            db.commit()
        
        # Simulate work (replace with actual logic)
        result = {
            "run_id": run_id,
            "status": "completed",
            "routing_changes": 47,
            "total_rewards_optimized": 1250,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        # Update run record
        if existing_run:
            existing_run.status = "done"
            existing_run.result = result
        else:
            db.query(RewardRoutingRun).filter(
                RewardRoutingRun.run_id == run_id
            ).update({
                "status": "done",
                "result": result
            })
        
        db.commit()
        
        logger.info(f"Reward routing rebalance completed", extra={
            "run_id": run_id,
            "job": "reward_routing_runner",
            "routing_changes": result["routing_changes"]
        })
        
        return result
        
    except Exception as e:
        # Mark as failed
        if existing_run:
            existing_run.status = "failed"
            existing_run.result = {"error": str(e)}
        else:
            db.query(RewardRoutingRun).filter(
                RewardRoutingRun.run_id == run_id
            ).update({
                "status": "failed",
                "result": {"error": str(e)}
            })
        
        db.commit()
        
        logger.error(f"Reward routing rebalance failed", extra={
            "run_id": run_id,
            "job": "reward_routing_runner",
            "error": str(e)
        })
        raise
    finally:
        db.close()
