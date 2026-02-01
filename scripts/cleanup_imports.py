#!/usr/bin/env python3
"""Script to identify and remove unused imports."""


import ast
import os
from typing import List, Tuple
import sys

class ImportAnalyzer(ast.NodeVisitor):

    """Analyze imports and usage in Python files."""

def __init__(self):

        self.imports = {}
        self.used_names = set()
        self.current_module = None

def visit_Import(self, node):

        """Track import statements."""
for alias in node.names:
            name = alias.asname or alias.name
            self.imports[name] = (node.lineno, alias.name)
        self.generic_visit(node)

def visit_ImportFrom(self, node):

        """Track from...import statements."""
for alias in node.names:
            name = alias.asname or alias.name
if name != "*":
                self.imports[name] = (node.lineno, f"from {node.module}")
        self.generic_visit(node)

def visit_Name(self, node):

        """Track name usage."""
        self.used_names.add(node.id)
        self.generic_visit(node)

def visit_Attribute(self, node):

        """Track attribute access."""
if isinstance(node.value, ast.Name):
            self.used_names.add(node.value.id)
        self.generic_visit(node)

def get_unused_imports(self) -> List[Tuple[str, int, str]]:

        """Return list of unused imports."""
        unused = []
for name, (lineno, source) in self.imports.items():
if name not in self.used_names and not name.startswith("_"):
                unused.append((name, lineno, source))
        return unused


def analyze_file(filepath: str) -> List[Tuple[str, int, str]]:

    """Analyze a Python file for unused imports."""
try:
with open(filepath, "r") as f:
            tree = ast.parse(f.read())
        analyzer = ImportAnalyzer()
        analyzer.visit(tree)
        return analyzer.get_unused_imports()
except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return []


def scan_directory(directory: str, extensions: List[str] = None) -> dict:

    """Scan directory for unused imports."""
if extensions is None:
        extensions = [".py"]

    results = {}
for root, dirs, files in os.walk(directory):
        # Skip common directories
        dirs[:] = [d for d in dirs if d not in ["__pycache__", ".git", "venv", ".venv"]]

for file in files:
if any(file.endswith(ext) for ext in extensions):
                filepath = os.path.join(root, file)
                unused = analyze_file(filepath)
if unused:
                    results[filepath] = unused

    return results


def print_report(results: dict):

    """Print analysis report."""
if not results:
        print("✅ No unused imports found!")
        return

    print(f"Found unused imports in {len(results)} files:\n")
    total_unused = 0

for filepath, unused in sorted(results.items()):
        print(f"📄 {filepath}")
for name, lineno, source in unused:
            print(f"   Line {lineno}: {name} (from {source})")
        total_unused += len(unused)

    print(f"\n📊 Total unused imports: {total_unused}")


if __name__ == "__main__":

    directory = sys.argv[1] if len(sys.argv) > 1 else "app"
    print(f"Scanning {directory} for unused imports...\n")

    results = scan_directory(directory)
    print_report(results)