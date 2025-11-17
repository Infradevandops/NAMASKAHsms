#!/usr/bin/env python3
"""
Secret Management Utility for Namaskah SMS

This script helps you manage environment variables and secrets securely.

Usage:
    python scripts/manage_secrets.py generate --env production
    python scripts/manage_secrets.py audit
    python scripts/manage_secrets.py validate --env production
    python scripts/manage_secrets.py rotate --key SECRET_KEY
"""

import argparse
import os
import sys
from pathlib import Path

from app.core.secrets import SecretsManager

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def generate_env_file(environment: str):
    """Generate a new environment file with secure secrets."""
    print(f"🔐 Generating environment file for {environment}...")

    output_path = f".env.{environment}"
    if Path(output_path).exists():
        response = input(f"File {output_path} already exists. Overwrite? (y/N): ")
        if response.lower() != "y":
            print("❌ Cancelled")
            return

    try:
        created_file = SecretsManager.create_env_file(environment, output_path)
        print(f"✅ Created {created_file}")
        print(f"📝 Please edit {created_file} and add your specific credentials")

        # Set secure permissions
        os.chmod(created_file, 0o600)
        print(f"🔒 Set secure permissions (600) on {created_file}")

    except Exception as e:
        print(f"❌ Error creating environment file: {e}")


def audit_environment():
    """Audit current environment for security issues."""
    print("🔍 Auditing environment security...")

    audit_result = SecretsManager.audit_environment()

    print(f"\n📊 Environment: {audit_result['environment']}")
    print(f"🔑 Secrets found: {audit_result['secrets_count']}")

    if audit_result["issues"]:
        print(f"\n❌ Issues found ({len(audit_result['issues'])}):")
        for issue in audit_result["issues"]:
            print(f"  • {issue}")

    if audit_result["warnings"]:
        print(f"\n⚠️ Warnings ({len(audit_result['warnings'])}):")
        for warning in audit_result["warnings"]:
            print(f"  • {warning}")

    if not audit_result["issues"] and not audit_result["warnings"]:
        print("\n✅ No security issues found!")

    return len(audit_result["issues"]) == 0


def validate_environment(environment: str = None):
    """Validate environment secrets."""
    if not environment:
        environment = os.getenv("ENVIRONMENT", "development")

    print(f"🔍 Validating {environment} environment...")

    try:
        SecretsManager.validate_required_secrets(environment)
        print("✅ All required secrets are present and valid")
        return True
    except ValueError as e:
        print(f"❌ Validation failed: {e}")
        return False


def rotate_secret(key: str):
    """Rotate a specific secret key."""
    print(f"🔄 Rotating secret: {key}")

    if key not in ["SECRET_KEY", "JWT_SECRET_KEY"]:
        print(
            f"❌ Cannot auto-rotate {key}. Only SECRET_KEY and JWT_SECRET_KEY are supported."
        )
        return

    # Generate new key
    new_value = SecretsManager.generate_secret_key()

    # Find and update in environment files
    env_files = [".env", ".env.production", ".env.staging", ".env.development"]
    updated_files = []

    for env_file in env_files:
        if Path(env_file).exists():
            try:
                content = Path(env_file).read_text()
                if f"{key}=" in content:
                    # Create backup
                    backup_file = f"{env_file}.backup"
                    Path(backup_file).write_text(content)

                    # Update the key
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if line.startswith(f"{key}="):
                            lines[i] = f"{key}={new_value}"
                            break

                    Path(env_file).write_text("\n".join(lines))
                    updated_files.append(env_file)
                    print(f"✅ Updated {env_file} (backup: {backup_file})")
            except Exception as e:
                print(f"❌ Error updating {env_file}: {e}")

    if updated_files:
        print(f"🔄 Rotated {key} in {len(updated_files)} files")
        print("⚠️ Remember to restart your application and update deployment secrets")
    else:
        print(f"❌ No files found containing {key}")


def list_secrets():
    """List all environment variables (masking sensitive ones)."""
    print("📋 Environment Variables:")

    for key, value in sorted(os.environ.items()):
        if SecretsManager.is_sensitive_key(key):
            masked_value = SecretsManager.mask_secret(value)
            print(f"  🔒 {key}={masked_value}")
        else:
            print(f"  📝 {key}={value}")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Manage secrets for Namaskah SMS")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate new environment file")
    gen_parser.add_argument(
        "--env",
        required=True,
        choices=["development", "staging", "production"],
        help="Environment to generate",
    )

    # Audit command
    subparsers.add_parser("audit", help="Audit current environment security")

    # Validate command
    val_parser = subparsers.add_parser("validate", help="Validate environment secrets")
    val_parser.add_argument("--env", help="Environment to validate")

    # Rotate command
    rot_parser = subparsers.add_parser("rotate", help="Rotate a secret key")
    rot_parser.add_argument("--key", required=True, help="Key to rotate")

    # List command
    subparsers.add_parser("list", help="List environment variables")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "generate":
            generate_env_file(args.env)
        elif args.command == "audit":
            success = audit_environment()
            return 0 if success else 1
        elif args.command == "validate":
            success = validate_environment(args.env)
            return 0 if success else 1
        elif args.command == "rotate":
            rotate_secret(args.key)
        elif args.command == "list":
            list_secrets()

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
