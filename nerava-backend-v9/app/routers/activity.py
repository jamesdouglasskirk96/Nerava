from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import get_db
from app.core.config import settings

router = APIRouter()

@router.get("/v1/activity")
async def get_activity_data(db: Session = Depends(get_db)):
    """Get user's activity data including reputation and follow earnings"""
    
    # For demo purposes, we'll use a hardcoded user ID
    # In production, this would come from authentication
    me = "demo-user-123"
    
    # Get current month
    from datetime import datetime
    month = int(datetime.now().strftime("%Y%m"))
    
    # Get reputation with streak_days and counts
    rep_query = text("SELECT score, tier, COALESCE(streak_days, 0), COALESCE(followers_count, 0), COALESCE(following_count, 0) FROM user_reputation WHERE user_id = :user_id")
    rep_result = db.execute(rep_query, {'user_id': me})
    rep_row = rep_result.fetchone()
    reputation = {
        'score': rep_row[0] if rep_row else 180,
        'tier': rep_row[1] if rep_row else 'Silver',
        'streakDays': rep_row[2] if rep_row else 7,
        'followers_count': rep_row[3] if rep_row else 12,
        'following_count': rep_row[4] if rep_row else 8
    }
    
    # Get earnings from monthly table (fallback to demo data)
    earn_query = text("""
        SELECT fem.payer_user_id AS user_id,
               COALESCE(u.handle,'member') AS handle,
               u.avatar_url,
               COALESCE(ur.tier,'Bronze') AS tier,
               fem.amount_cents,
               fem.context
        FROM follow_earnings_monthly fem
        LEFT JOIN users u ON u.id = fem.payer_user_id
        LEFT JOIN user_reputation ur ON ur.user_id = fem.payer_user_id
        WHERE fem.month_yyyymm = :month AND fem.receiver_user_id = :user_id
        ORDER BY fem.amount_cents DESC
    """)
    
    earn_result = db.execute(earn_query, {'month': month, 'user_id': me})
    earnings = []
    total_cents = 0
    
    for row in earn_result:
        earnings.append({
            'userId': row[0],
            'handle': row[1],
            'avatarUrl': row[2],
            'tier': row[3],
            'amountCents': int(row[4]),
            'context': row[5]
        })
        total_cents += int(row[4])
    
    # If no earnings found, return demo data
    if not earnings:
        earnings = [
            {
                'userId': 'demo-user-1',
                'handle': 'alex',
                'avatarUrl': None,
                'tier': 'Gold',
                'amountCents': 185,
                'context': 'charged and chilled at Starbucks'
            },
            {
                'userId': 'demo-user-2',
                'handle': 'sam', 
                'avatarUrl': None,
                'tier': 'Bronze',
                'amountCents': 90,
                'context': 'topped up at Target'
            },
            {
                'userId': 'demo-user-3',
                'handle': 'riley',
                'avatarUrl': None,
                'tier': 'Silver',
                'amountCents': 75,
                'context': 'smart-charged at Whole Foods'
            },
            {
                'userId': 'demo-user-4',
                'handle': 'jordan',
                'avatarUrl': None,
                'tier': 'Gold',
                'amountCents': 120,
                'context': 'queued and earned at H-E-B'
            },
            {
                'userId': 'demo-user-5',
                'handle': 'morgan',
                'avatarUrl': None,
                'tier': 'Bronze',
                'amountCents': 60,
                'context': 'plugged in at Costco'
            }
        ]
        total_cents = 530
    
    return {
        'month': month,
        'reputation': reputation,
        'followEarnings': earnings,
        'totals': {
            'followCents': total_cents
        }
    }

@router.post("/v1/session/verify")
async def verify_session(session_data: dict, db: Session = Depends(get_db)):
    """Verify a charging session and trigger auto-follow + rewards"""
    
    # For demo purposes, we'll use hardcoded values
    me = "demo-user-123"
    session_id = session_data.get('sessionId', str(uuid.uuid4()))
    station_id = session_data.get('stationId', 'STATION_A')
    energy_kwh = session_data.get('energyKwh', 15.0)
    
    # Get session details
    session_query = text("""
        SELECT id, user_id, station_id, start_at, energy_kwh 
        FROM sessions 
        WHERE id = :session_id AND user_id = :user_id
    """)
    
    session_result = db.execute(session_query, {
        'session_id': session_id,
        'user_id': me
    })
    
    session_row = session_result.fetchone()
    if not session_row:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Trigger auto-follow
    from app.services.activity import auto_follow_on_verified_session, reward_followers_for_session
    
    await auto_follow_on_verified_session(me, station_id, session_row[3])
    await reward_followers_for_session(me, session_id, station_id, float(session_row[4] or 0))
    
    return {"ok": True}
