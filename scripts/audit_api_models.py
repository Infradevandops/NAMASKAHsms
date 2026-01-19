"""Audit API responses against model fields."""

import ast
import os
import re


def get_model_fields(model_file):
    """Extract Column fields from SQLAlchemy model."""
    if not os.path.exists(model_file):
        return []

    with open(model_file) as f:
        tree = ast.parse(f.read())

    fields = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    fields.append(target.id)
    return fields


def get_api_response_fields(api_file):
    """Extract response dict keys from API file."""
    if not os.path.exists(api_file):
        return []

    with open(api_file) as f:
        content = f.read()

    # Simple regex to find dict keys in return statements or dict construction
    # Matches "key": value or 'key': value
    keys = re.findall(r'["\'](\w+)["\']:', content)
    return list(set(keys))


def audit():
    """Run audit."""
    models = {
        "User": "app/models/user.py",
        "Verification": "app/models/verification.py",
        "AuditLog": "app/models/audit_log.py",
    }

    apis = [
        "app/api/admin/verification_history.py",
        "app/api/admin/user_management.py",
        "app/api/admin/audit_compliance.py",
        "app/api/core/auth.py",
        "app/api/billing/payment_endpoints.py",
    ]

    print("=== Model-API Alignment Audit ===\n")

    for api_file in apis:
        if not os.path.exists(api_file):
            print(f"Skipping {api_file} (not found)")
            continue

        print(f"\n📄 {api_file}")
        api_fields = get_api_response_fields(api_file)
        print(f"   Response fields ({len(api_fields)}): {api_fields[:10]}...")

        # We could compare with model fields if we knew which model corresponds to which API
        # For now just printing as per instructions.


if __name__ == "__main__":
    audit()
