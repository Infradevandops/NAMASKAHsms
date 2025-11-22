#!/usr/bin/env python3
"""Script to fix code quality issues automatically."""
import re
import ast
from pathlib import Path


def fix_resource_leaks():
    """Fix resource leaks by ensuring proper context managers."""
    fixes_applied = 0
    
    for py_file in Path("app").rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Fix file operations without context managers
            content = re.sub(
                r'(\w+)\s*=\s*open\(([^)]+)\)\s*\n',
                r'with open(\2) as \1:\n',
                content
            )
            
            # Fix database connections without proper closing
            content = re.sub(
                r'conn\s*=\s*([^.]+\.connect\([^)]+\))\s*\n',
                r'with \1 as conn:\n',
                content
            )
            
            if content != original_content:
                with open(py_file, 'w') as f:
                    f.write(content)
                print(f"Fixed resource leaks in {py_file}")
                fixes_applied += 1
                
        except Exception as e:
            print(f"Error processing {py_file}: {e}")
    
    return fixes_applied


def fix_string_operations():
    """Fix inefficient string operations."""
    fixes_applied = 0
    
    for py_file in Path("app").rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Fix string concatenation in loops
            content = re.sub(
                r'(\w+)\s*\+=\s*([^+\n]+)\s*\+\s*([^\n]+)',
                r'\1 = "".join([\1, \2, \3])',
                content
            )
            
            # Fix multiple string concatenations
            content = re.sub(
                r'(["\'][^"\']*["\'])\s*\+\s*(["\'][^"\']*["\'])\s*\+\s*(["\'][^"\']*["\'])',
                r'f"\1\2\3"',
                content
            )
            
            if content != original_content:
                with open(py_file, 'w') as f:
                    f.write(content)
                print(f"Fixed string operations in {py_file}")
                fixes_applied += 1
                
        except Exception as e:
            print(f"Error processing {py_file}: {e}")
    
    return fixes_applied


def fix_identity_equality_issues():
    """Fix identity vs equality confusion."""
    fixes_applied = 0
    
    for py_file in Path("app").rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Fix 'is' used with literals (except None, True, False)
            patterns = [
                (r'\bis\s+([0-9]+)', r'== \1'),
                (r'\bis\s+([\'""][^\'""]*[\'""])', r'== \1'),
                (r'\bis\s+(\[[^\]]*\])', r'== \1'),
                (r'\bis\s+(\{[^}]*\})', r'== \1'),
            ]
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
            
            # Fix 'is not' with literals
            patterns = [
                (r'\bis\s+not\s+([0-9]+)', r'!= \1'),
                (r'\bis\s+not\s+([\'""][^\'""]*[\'""])', r'!= \1'),
                (r'\bis\s+not\s+(\[[^\]]*\])', r'!= \1'),
                (r'\bis\s+not\s+(\{[^}]*\})', r'!= \1'),
            ]
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
            
            if content != original_content:
                with open(py_file, 'w') as f:
                    f.write(content)
                print(f"Fixed identity/equality issues in {py_file}")
                fixes_applied += 1
                
        except Exception as e:
            print(f"Error processing {py_file}: {e}")
    
    return fixes_applied


def apply_pep8_fixes():
    """Apply basic PEP8 fixes."""
    fixes_applied = 0
    
    for py_file in Path("app").rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Fix line length (basic cases)
            lines = content.split('\n')
            fixed_lines = []
            
            for line in lines:
                if len(line) > 88 and '"""' not in line and "'''" not in line:
                    # Simple line breaking for long lines
                    if ' and ' in line and len(line) > 88:
                        line = line.replace(' and ', ' and \\\n    ')
                    elif ' or ' in line and len(line) > 88:
                        line = line.replace(' or ', ' or \\\n    ')
                    elif ', ' in line and len(line) > 88:
                        # Break at commas
                        parts = line.split(', ')
                        if len(parts) > 2:
                            mid = len(parts) // 2
                            line = ', '.join(parts[:mid]) + ',\n    ' + ', '.join(parts[mid:])
                
                fixed_lines.append(line)
            
            content = '\n'.join(fixed_lines)
            
            # Fix spacing around operators
            content = re.sub(r'(\w+)=(\w+)', r'\1 = \2', content)
            content = re.sub(r'(\w+)\+(\w+)', r'\1 + \2', content)
            content = re.sub(r'(\w+)-(\w+)', r'\1 - \2', content)
            
            # Fix trailing whitespace
            content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
            
            # Fix multiple blank lines
            content = re.sub(r'\n\n\n+', '\n\n', content)
            
            if content != original_content:
                with open(py_file, 'w') as f:
                    f.write(content)
                print(f"Applied PEP8 fixes to {py_file}")
                fixes_applied += 1
                
        except Exception as e:
            print(f"Error processing {py_file}: {e}")
    
    return fixes_applied


def check_cyclomatic_complexity():
    """Check and report cyclomatic complexity."""
    complex_functions = []
    
    for py_file in Path("app").rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = calculate_complexity(node)
                    if complexity > 10:
                        complex_functions.append((str(py_file), node.name, complexity))
        
        except Exception as e:
            print(f"Error analyzing {py_file}: {e}")
    
    return complex_functions


def calculate_complexity(node):
    """Calculate cyclomatic complexity of a function."""
    complexity = 1  # Base complexity
    
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, (ast.And, ast.Or)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    
    return complexity


def main():
    """Run all code quality fixes."""
    print("🔧 Starting code quality fixes...")
    
    print("\n1. Fixing resource leaks...")
    resource_fixes = fix_resource_leaks()
    print(f"   Applied {resource_fixes} resource leak fixes")
    
    print("\n2. Fixing string operations...")
    string_fixes = fix_string_operations()
    print(f"   Applied {string_fixes} string operation fixes")
    
    print("\n3. Fixing identity/equality issues...")
    identity_fixes = fix_identity_equality_issues()
    print(f"   Applied {identity_fixes} identity/equality fixes")
    
    print("\n4. Applying PEP8 fixes...")
    pep8_fixes = apply_pep8_fixes()
    print(f"   Applied {pep8_fixes} PEP8 fixes")
    
    print("\n5. Checking cyclomatic complexity...")
    complex_functions = check_cyclomatic_complexity()
    if complex_functions:
        print("   Functions with high complexity (>10):")
        for file_path, func_name, complexity in complex_functions:
            print(f"     {file_path}:{func_name} - {complexity}")
    else:
        print("   ✅ All functions have acceptable complexity (<10)")
    
    total_fixes = resource_fixes + string_fixes + identity_fixes + pep8_fixes
    print(f"\n✅ Code quality fixes complete! Applied {total_fixes} total fixes.")
    
    return total_fixes


if __name__ == "__main__":
    main()