"""
Add __repr__ to SQLAlchemy model classes that are missing it.
Uses AST to find classes, then inserts __repr__ before the first method or at end of class.
"""
import ast
import os

MODEL_DIR = "app/models"
SKIP_FILES = {"__init__.py", "base.py"}


def get_primary_key_field(class_node):
    """Try to find a good field to use in __repr__: id, email, name, or first column."""
    candidates = []
    for node in ast.walk(class_node):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    candidates.append(target.id)
    # Prefer id, then email, then name, then first candidate
    for preferred in ("id", "email", "name", "slug", "title"):
        if preferred in candidates:
            return preferred
    return candidates[0] if candidates else "id"


def add_repr_to_file(path):
    with open(path) as f:
        src = f.read()

    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return 0, f"parse error: {e}"

    lines = src.splitlines(keepends=True)
    added = 0

    # Process classes in reverse order to preserve line numbers
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    classes.sort(key=lambda n: n.lineno, reverse=True)

    for cls in classes:
        # Skip if already has __repr__
        method_names = [n.name for n in ast.walk(cls) if isinstance(n, ast.FunctionDef)]
        if "__repr__" in method_names:
            continue

        # Skip non-model classes (no Column assignments)
        has_column = any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Column"
            for n in ast.walk(cls)
        ) or any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("Column", "mapped_column")
            for n in ast.walk(cls)
        )
        if not has_column:
            continue

        field = get_primary_key_field(cls)
        class_name = cls.name

        # Build __repr__ method (4-space indent inside class)
        repr_lines = [
            "\n",
            f"    def __repr__(self) -> str:\n",
            f'        return f"<{class_name} {field}={{self.{field}}}>"\n',
        ]

        # Insert before first method, or at end of class body
        insert_at = cls.end_lineno  # default: end of class (0-indexed: end_lineno - 1)

        # Find first method line
        for node in cls.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                insert_at = node.lineno - 1  # insert before this line (0-indexed)
                break

        lines[insert_at:insert_at] = repr_lines
        added += 1

    if added == 0:
        return 0, "nothing to add"

    new_src = "".join(lines)

    # Validate
    try:
        ast.parse(new_src)
    except SyntaxError as e:
        return 0, f"syntax error after transform: {e}"

    with open(path, "w") as f:
        f.write(new_src)

    return added, f"added {added} __repr__"


total = 0
for fname in sorted(os.listdir(MODEL_DIR)):
    if fname in SKIP_FILES or not fname.endswith(".py"):
        continue
    path = os.path.join(MODEL_DIR, fname)
    count, msg = add_repr_to_file(path)
    if count:
        print(f"OK   {path}: {msg}")
        total += count
    else:
        print(f"SKIP {path}: {msg}")

print(f"\nTotal __repr__ added: {total}")
