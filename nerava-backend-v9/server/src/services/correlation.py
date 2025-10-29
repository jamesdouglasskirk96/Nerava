from datetime import timedelta
from ..config import Config

def correlation_score(session, pos, cfg: Config):
    """
    Calculate correlation score between session and POS event.
    Returns score 0.0 to 1.0
    """
    score = 0.0
    
    # Confidence component (0.6 max)
    conf = (session.confidence or "NONE").upper()
    if conf == "HIGH":
        score += 0.6
    elif conf == "MEDIUM":
        score += 0.3
    
    # Time proximity component (0.3 max)
    pivot = session.end_at or session.t0
    dt_min = abs((pos.t_event - pivot).total_seconds() / 60.0)
    time_component = max(0.0, 0.3 - min(dt_min, 30.0) / 100.0)
    score += time_component
    
    # Optional spatial component can be added later (0.1 max)
    
    return min(score, 1.0)

def approved(session, pos, cfg: Config):
    """
    Check if session + POS event should be approved for reward.
    Returns (is_approved, score, reason)
    """
    # Time window check
    early = session.t0 - timedelta(minutes=15)
    late = session.t0 + timedelta(minutes=cfg.VERIFICATION_WINDOW_MIN)
    if not (early <= pos.t_event <= late):
        return (False, 0.0, "outside_time_window")
    
    # Charge verification check
    if not session.verified_charge and not cfg.ALLOW_MERCHANT_DWELL_FALLBACK:
        return (False, 0.0, "unverified_charge")
    
    # Score calculation
    score = correlation_score(session, pos, cfg)
    if score >= 0.75:
        return (True, score, "ok")
    else:
        return (False, score, "low_score")
