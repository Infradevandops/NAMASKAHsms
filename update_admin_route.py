#!/usr/bin/env python3
import re

with open('main.py', 'r') as f:
    content = f.read()

# Find and replace the admin_dashboard function
pattern = r'@fastapi_app\.get\("/admin", response_class=HTMLResponse\)\s+async def admin_dashboard\(request: Request, db: Session = Depends\(get_db\)\):.*?return RedirectResponse\(url=\'/auth/login\?error=server_error&redirect=/admin\', status_code=302\)'

replacement = '''@fastapi_app.get("/admin", response_class=HTMLResponse)
    async def admin_dashboard(request: Request, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        return templates.TemplateResponse("admin/dashboard.html", {"request": request, "user": user})'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('main.py', 'w') as f:
    f.write(content)

print("✅ Admin route updated successfully")
