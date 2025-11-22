#!/usr/bin/env python3
"""Add dashboard route to main.py"""
import re

with open('main.py', 'r') as f:
    content = f.read()

new_route = '''
    @fastapi_app.get("/dashboard-complete", response_class=HTMLResponse)
    async def dashboard_complete(user_id: Optional[str] = Depends(get_optional_user_id)):
        if not user_id:
            return HTMLResponse(content="<h1>🔒 Authentication Required</h1>")
        return HTMLResponse(content=_load_template("dashboard_complete.html"))
'''

# Find the verify_page function and insert after it
pattern = r'(    @fastapi_app\.get\("/verify".*?return HTMLResponse\(content=_load_template\("verification_enhanced\.html"\)\))'
match = re.search(pattern, content, re.DOTALL)

if match:
    insert_pos = match.end()
    content = content[:insert_pos] + new_route + content[insert_pos:]
    
    with open('main.py', 'w') as f:
        f.write(content)
    print("✅ Dashboard route added")
else:
    print("❌ Could not find insertion point")
