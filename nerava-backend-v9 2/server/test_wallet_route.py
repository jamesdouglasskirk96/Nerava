@router.get("/wallet/summary")
def wallet_summary(user_id: str = Depends(current_user_id), db: Session = Depends(get_db)):
    """Simplified wallet summary for debugging"""
    try:
        # Get wallet events
        wallet_rows = db.query(WalletEvent).filter(WalletEvent.user_id==user_id).order_by(WalletEvent.created_at.desc()).all()
        
        # Calculate balance from wallet events only
        balance = sum(r.amount_cents if r.type=="earn" else -r.amount_cents for r in wallet_rows)
        
        # Simple breakdown
        breakdown = [ {"title":r.title, "amountCents": r.amount_cents, "type": r.type} for r in wallet_rows[:5] ]
        
        return {"balanceCents": balance, "breakdown": breakdown, "history": breakdown}
        
    except Exception as e:
        print(f"Wallet summary error: {e}")
        import traceback
        traceback.print_exc()
        return {"balanceCents": 0, "breakdown": [], "history": []}
