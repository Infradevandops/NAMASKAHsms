"""
Add try/except error handling to FastAPI endpoint functions that lack it.
Uses AST to find exact function body line ranges, then does text insertion.
"""
import ast
import os
import textwrap

FILES = [
    "app/api/core/preferences.py",
    "app/api/core/quotas.py",
    "app/api/core/user_profile.py",
    "app/api/core/user_insights.py",
    "app/api/core/webhooks.py",
    "app/api/core/notifications.py",
    "app/api/core/api_key_endpoints.py",
    "app/api/admin/analytics_reports.py",
    "app/api/admin/audit_unreceived.py",
    "app/api/admin/disaster_recovery.py",
    "app/api/admin/gdpr_admin.py",
    "app/api/admin/monitoring.py",
    "app/api/admin/verification_history.py",
    "app/api/billing/history.py",
    "app/api/billing/invoice_endpoints.py",
    "app/api/billing/payment_method_endpoints.py",
    "app/api/verification/outcome_endpoint.py",
    "app/api/verification/preset_endpoints.py",
]


def process_file(path):
    with open(path) as f:
        src = f.read()

    if "try:" in src:
        return False, "already has try/except"

    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return False, f"parse error: {e}"

    lines = src.splitlines(keepends=True)

    # Find all top-level async def functions decorated with @router.*
    # Collect (func_node, has_router_decorator) pairs
    router_funcs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            # Check decorators
            for dec in node.decorator_list:
                dec_src = ast.unparse(dec) if hasattr(ast, "unparse") else ""
                if "router." in dec_src:
                    router_funcs.append(node)
                    break

    if not router_funcs:
        return False, "no router-decorated functions found"

    # Sort by line number descending so insertions don't shift earlier lines
    router_funcs.sort(key=lambda n: n.lineno, reverse=True)

    for func in router_funcs:
        # func.body gives us the list of statements
        # func.body[0] may be a docstring — skip it for indentation purposes
        body_stmts = func.body

        # Already has try — skip
        if any(isinstance(s, ast.Try) for s in body_stmts):
            continue

        # Find first and last line of the body (1-indexed)
        body_start = body_stmts[0].lineno   # first statement line
        # end_lineno available in Python 3.8+
        body_end = func.end_lineno

        # Determine indentation of body (4 spaces inside function)
        indent = "    "

        # Extract body lines (0-indexed: body_start-1 to body_end-1)
        body_lines = lines[body_start - 1 : body_end]

        # Build new body: try: + indented body + except clauses
        new_body = []
        new_body.append(f"{indent}try:\n")
        for bl in body_lines:
            if bl.strip() == "":
                new_body.append("\n")
            else:
                new_body.append(f"{indent}{bl}")
        new_body.append(f"{indent}except HTTPException:\n")
        new_body.append(f"{indent}    raise\n")
        new_body.append(f"{indent}except Exception as e:\n")
        new_body.append(f'{indent}    logger.error(f"Error in {func.name}: {{e}}", exc_info=True)\n')
        new_body.append(f'{indent}    raise HTTPException(status_code=500, detail="Internal server error")\n')

        # Replace lines in the file
        lines[body_start - 1 : body_end] = new_body

    new_src = "".join(lines)

    # Add logger if missing
    if "import logging" not in new_src and "get_logger" not in new_src:
        new_src = "import logging\nlogger = logging.getLogger(__name__)\n" + new_src
    elif "logger" not in new_src:
        # Has logging import but no logger instance
        new_src = new_src.replace(
            "import logging\n",
            "import logging\nlogger = logging.getLogger(__name__)\n",
            1,
        )

    # Add HTTPException import if missing
    if "HTTPException" not in new_src:
        # Insert after first 'from fastapi import' line
        new_src = new_src.replace(
            "from fastapi import",
            "from fastapi import HTTPException  # noqa\nfrom fastapi import",
            1,
        )

    # Validate syntax
    try:
        ast.parse(new_src)
    except SyntaxError as e:
        return False, f"syntax error after transform: {e}"

    with open(path, "w") as f:
        f.write(new_src)

    return True, f"wrapped {len(router_funcs)} endpoint(s)"


for f in FILES:
    ok, msg = process_file(f)
    print(f"{'OK  ' if ok else 'SKIP'} {f}: {msg}")
