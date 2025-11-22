#!/usr/bin/env python3
"""Validate migration chain integrity."""

import re
from pathlib import Path
from typing import Dict, List, Tuple

MIGRATIONS_DIR = Path("alembic/versions")


def parse_migration(file_path: Path) -> Dict:
    """Parse migration file for revision info."""
    with open(file_path) as f:
        content = f.read()

    revision_match = re.search(r'revision\s*=\s*["\']([^"\']+)["\']', content)
    down_revision_match = re.search(r'down_revision\s*=\s*(.+?)(?:\n|$)', content)

    revision = revision_match.group(1) if revision_match else None
    down_revision_str = down_revision_match.group(1) if down_revision_match else None

    # Parse down_revision (can be single or tuple)
    down_revisions = []
    if down_revision_str:
        if down_revision_str.strip() == "None":
            down_revisions = []
        elif "(" in down_revision_str:
            # Tuple format: ("001", "002")
            matches = re.findall(r'["\']([^"\']+)["\']', down_revision_str)
            down_revisions = matches
        else:
            # Single format: "001"
            match = re.search(r'["\']([^"\']+)["\']', down_revision_str)
            if match:
                down_revisions = [match.group(1)]

    return {
        "file": file_path.name,
        "revision": revision,
        "down_revisions": down_revisions,
    }


def validate_migrations() -> Tuple[bool, List[str]]:
    """Validate migration chain."""
    issues = []

    # Get all migration files
    migration_files = sorted(MIGRATIONS_DIR.glob("*.py"))
    if not migration_files:
        issues.append("❌ No migration files found")
        return False, issues

    migrations = {}
    for file_path in migration_files:
        if file_path.name.startswith("__"):
            continue
        migration = parse_migration(file_path)
        if migration["revision"]:
            migrations[migration["revision"]] = migration

    # Check for circular dependencies
    visited = set()
    rec_stack = set()

    def has_cycle(rev: str, path: List[str]) -> bool:
        visited.add(rev)
        rec_stack.add(rev)
        path.append(rev)

        migration = migrations.get(rev)
        if not migration:
            return False

        for down_rev in migration["down_revisions"]:
            if down_rev not in visited:
                if has_cycle(down_rev, path.copy()):
                    return True
            elif down_rev in rec_stack:
                issues.append(f"❌ Circular dependency detected: {' → '.join(path)} → {down_rev}")
                return True

        rec_stack.discard(rev)
        return False

    # Check each migration
    for rev in migrations:
        if rev not in visited:
            has_cycle(rev, [])

    # Check for multiple down_revisions (merge migrations)
    for rev, migration in migrations.items():
        if len(migration["down_revisions"]) > 1:
            issues.append(
                f"⚠️  Merge migration detected: {migration['file']} "
                f"has multiple down_revisions: {migration['down_revisions']}"
            )

    # Check for orphaned migrations
    all_revisions = set(migrations.keys())
    referenced_revisions = set()
    for migration in migrations.values():
        referenced_revisions.update(migration["down_revisions"])

    orphaned = referenced_revisions - all_revisions
    if orphaned:
        issues.append(f"❌ Orphaned down_revisions (not found): {orphaned}")

    # Check for duplicate revisions
    revisions_list = [m["revision"] for m in migrations.values()]
    duplicates = [r for r in revisions_list if revisions_list.count(r) > 1]
    if duplicates:
        issues.append(f"❌ Duplicate revisions found: {set(duplicates)}")

    return len(issues) == 0, issues


if __name__ == "__main__":
    print("🔍 Validating migration chain...\n")

    is_valid, issues = validate_migrations()

    if issues:
        for issue in issues:
            print(issue)
        print(f"\n❌ Validation failed with {len(issues)} issue(s)")
        exit(1)
    else:
        print("✅ Migration chain is valid!")
        exit(0)
