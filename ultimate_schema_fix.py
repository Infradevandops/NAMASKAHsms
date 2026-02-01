#!/usr/bin/env python3
"""
ULTIMATE SCHEMA FIX - Final push to 100% CI/CD success
"""

import os
import re
import ast

def fix_schema_file(file_path):
    """Fix all syntax issues in a schema file."""
    if not os.path.exists(file_path):
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        lines = content.splitlines()
        fixed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines
            if not line.strip():
                fixed_lines.append(line)
                i += 1
                continue
            
            # Fix @classmethod decorator followed by malformed def
            if line.strip() == '@classmethod' and i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.strip().startswith('def ') and not next_line.startswith('    def'):
                    fixed_lines.append('    @classmethod')
                    fixed_lines.append('    ' + next_line.strip())
                    i += 2
                    continue
            
            # Fix @field_validator decorator followed by malformed def
            if line.strip().startswith('@field_validator') and i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.strip() == '@classmethod' and i + 2 < len(lines):
                    def_line = lines[i + 2]
                    if def_line.strip().startswith('def ') and not def_line.startswith('    def'):
                        fixed_lines.append('    ' + line.strip())
                        fixed_lines.append('    @classmethod')
                        fixed_lines.append('    ' + def_line.strip())
                        i += 3
                        continue
            
            # Fix standalone function definitions that should be methods
            if re.match(r'^def \w+\(cls,', line.strip()) and not line.startswith('    def'):
                fixed_lines.append('    ' + line.strip())
                i += 1
                continue
            
            # Fix if statements that should be indented
            if line.strip().startswith('if ') and not line.startswith('    if ') and not line.startswith('if '):
                # Check if we're inside a function
                if i > 0 and any('def ' in fixed_lines[j] for j in range(max(0, i-5), i)):
                    fixed_lines.append('        ' + line.strip())
                else:
                    fixed_lines.append(line)
                i += 1
                continue
            
            # Fix return statements
            if line.strip().startswith('return ') and not line.startswith('    return ') and not line.startswith('return '):
                if i > 0 and any('def ' in fixed_lines[j] for j in range(max(0, i-5), i)):
                    fixed_lines.append('        ' + line.strip())
                else:
                    fixed_lines.append(line)
                i += 1
                continue
            
            # Fix raise statements
            if line.strip().startswith('raise ') and not line.startswith('        raise'):
                fixed_lines.append('            ' + line.strip())
                i += 1
                continue
            
            # Default: keep the line as is
            fixed_lines.append(line)
            i += 1
        
        # Write back the fixed content
        with open(file_path, 'w') as f:
            f.write('\n'.join(fixed_lines))
            if fixed_lines:
                f.write('\n')
        
        # Validate syntax
        try:
            with open(file_path, 'r') as f:
                ast.parse(f.read())
            print(f"✅ {file_path} - Fixed and validated")
            return True
        except (SyntaxError, IndentationError) as e:
            print(f"❌ {file_path} - Still has error: Line {e.lineno}: {e.msg}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Fix all schema files."""
    print("🚀 ULTIMATE SCHEMA FIX")
    print("=" * 50)
    
    schema_files = [
        'app/schemas/auth.py',
        'app/schemas/validators.py', 
        'app/schemas/payment.py',
        'app/schemas/kyc.py',
        'app/schemas/tier.py',
        'app/schemas/tier_validators.py',
        'app/schemas/verification.py',
        'app/schemas/analytics.py',
        'app/schemas/system.py'
    ]
    
    fixed_count = 0
    for file_path in schema_files:
        if fix_schema_file(file_path):
            fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count}/{len(schema_files)} schema files")
    
    if fixed_count == len([f for f in schema_files if os.path.exists(f)]):
        print("🎉 ALL SCHEMA FILES ARE NOW SYNTACTICALLY CORRECT!")
        print("✅ Ready for 100% CI/CD success!")
        return True
    else:
        print("❌ Some files still need manual intervention")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)