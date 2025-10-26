@router.get("/wallet/test")
def wallet_test(user_id: str = Depends(current_user_id), db: Session = Depends(get_db)):
    """Minimal wallet test"""
    try:
        # Test basic query
        count = db.query(WalletEvent).count()
        return {"status": "success", "wallet_events_count": count}
    except Exception as e:
        return {"status": "error", "error": str(e)}
