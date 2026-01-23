@router.get("/payments/test2")
async def test_payments2(
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db)
):
    """Test payments query with data"""
    try:
        result = db.execute(text("""
            SELECT id, merchant_id, status, amount_cents, created_at
            FROM payments 
            WHERE user_id = :user_id 
            ORDER BY created_at DESC 
            LIMIT 5
        """), {'user_id': user_id})
        
        payments = []
        for row in result:
            payments.append({
                'id': row[0],
                'merchantId': row[1],
                'status': row[2],
                'amountCents': row[3],
                'createdAt': str(row[4]) if row[4] else None
            })
        
        return {"status": "success", "payments": payments}
    except Exception as e:
        return {"status": "error", "error": str(e)}
