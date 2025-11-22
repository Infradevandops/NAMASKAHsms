@fastapi_app.post("/api/billing/add-credits")
async def add_credits(request: Request, user_id: Optional[str] = Depends(get_optional_user_id), db: Session = Depends(get_db)):
    from app.models.user import User
    import json
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        body = await request.body()
        data = json.loads(body)
        amount = float(data.get("amount", 0))
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid amount")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        bonus = 7 if amount >= 50 else (3 if amount >= 25 else (1 if amount >= 10 else 0))
        total_amount = amount + bonus
        user.credits = (user.credits or 0) + total_amount
        db.commit()
        return {"success": True, "amount_added": total_amount, "bonus": bonus, "new_balance": float(user.credits)}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
