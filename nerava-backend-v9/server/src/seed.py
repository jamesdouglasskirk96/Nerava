# server/src/seed.py
from .db import engine, SessionLocal, Base
from .models import User, Reputation, FollowEarning, WalletEvent
from datetime import datetime
from uuid import uuid4

def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    DEMO = "user-demo-1"
    alex = "user-alex"
    sam = "user-sam"

    for u, handle in [(DEMO,"you"), (alex,"alex"), (sam,"sam")]:
        if not db.get(User, u):
            db.add(User(id=u, handle=handle, followers=12 if u==DEMO else 3, following=8 if u==DEMO else 2))
    if not db.get(Reputation, DEMO):
        db.add(Reputation(user_id=DEMO, score=180, tier="Silver"))

    month = int(datetime.utcnow().strftime("%Y%m"))
    if not db.query(FollowEarning).filter_by(month_yyyymm=month, receiver_user_id=DEMO).first():
        db.add_all([
            FollowEarning(month_yyyymm=month, receiver_user_id=DEMO, payer_user_id=alex, amount_cents=185),
            FollowEarning(month_yyyymm=month, receiver_user_id=DEMO, payer_user_id=sam, amount_cents=90),
        ])

    if not db.query(WalletEvent).filter_by(user_id=DEMO).first():
        db.add_all([
            WalletEvent(id=str(uuid4()), user_id=DEMO, kind="credit", source="green_hour", amount_cents=373, meta={"title": "Green Hour savings"}),
            WalletEvent(id=str(uuid4()), user_id=DEMO, kind="credit", source="merchant_reward", amount_cents=75, meta={"title": "Starbucks co-fund"}),
            WalletEvent(id=str(uuid4()), user_id=DEMO, kind="debit", source="off_peak", amount_cents=50, meta={"title": "Off-peak award"}),
            WalletEvent(id=str(uuid4()), user_id=DEMO, kind="credit", source="merchant_reward", amount_cents=100, meta={"title": "McDonald's reward"}),
            WalletEvent(id=str(uuid4()), user_id=DEMO, kind="debit", source="payment", amount_cents=500, meta={"title": "Payment @ Starbucks"}),
        ])
    db.commit(); db.close()

if __name__ == "__main__":
    run()
