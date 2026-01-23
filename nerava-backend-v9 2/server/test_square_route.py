@router.get("/payments/test")
async def test_payments(
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db)
):
    """Test payments query"""
    try:
        result = db.execute(text("SELECT COUNT(*) FROM payments WHERE user_id = :user_id"), {'user_id': user_id})
        count = result.fetchone()[0]
        return {"status": "success", "count": count}
    except Exception as e:
        return {"status": "error", "error": str(e)}
