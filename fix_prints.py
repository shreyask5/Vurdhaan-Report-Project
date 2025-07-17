#!/usr/bin/env python3
"""
Script to replace debug_print calls with regular print statements
"""

def fix_debug_prints():
    """Replace all debug_print calls with regular print calls"""
    
    # Read the file
    with open('app4.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace debug_print( with print(
    content = content.replace('debug_print(', 'print(')
    
    # Ensure all print statements have flush=True
    # This regex finds print statements without flush=True and adds it
    import re
    
    # Pattern to find print statements that don't already have flush=True
    pattern = r'print\(([^)]+)\)(?!, flush=True)'
    
    def add_flush(match):
        args = match.group(1)
        return f'print({args}, flush=True)'
    
    # Apply the replacement
    content = re.sub(pattern, add_flush, content)
    
    # Write the file back
    with open('app4.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed all debug_print calls in app4.py")
    print("✅ Added flush=True to all print statements")

if __name__ == "__main__":
    fix_debug_prints() 