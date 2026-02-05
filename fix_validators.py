#!/usr/bin/env python3
"""Fix validators.py indentation issues."""

import re

def fix_validators_file():
    """Fix all indentation issues in validators.py."""
    with open('app/schemas/validators.py', 'r') as f:
        content = f.read()
    
    lines = content.splitlines()
    fixed_lines = []
    in_function = False
    function_indent = 0
    
    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue
        
        # Detect function definitions
        if line.strip().startswith('def '):
            in_function = True
            function_indent = 0
            fixed_lines.append(line)
            continue
        
        # Handle docstrings
        if '"""' in line and in_function:
            if function_indent == 0:
                fixed_lines.append('    ' + line.strip())
            else:
                fixed_lines.append(line)
            continue
        
        # Handle function body
        if in_function:
            stripped = line.strip()
            
            # If this is a new function, reset
            if stripped.startswith('def '):
                in_function = True
                function_indent = 0
                fixed_lines.append(line)
                continue
            
            # If this is a class definition, we're out of function
            if stripped.startswith('class '):
                in_function = False
                fixed_lines.append(line)
                continue
            
            # Handle function content
            if stripped:
                # Ensure proper indentation for function body
                if not line.startswith('    '):
                    fixed_lines.append('    ' + stripped)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Write back the fixed content
    with open('app/schemas/validators.py', 'w') as f:
        f.write('\n'.join(fixed_lines))
        if fixed_lines:
            f.write('\n')
    
    print("✅ Fixed validators.py indentation")

if __name__ == '__main__':
    fix_validators_file()
