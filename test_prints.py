#!/usr/bin/env python3
"""
Test script to verify print statements are visible in console
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_print(message: str):
    """Print debug message that's guaranteed to be visible in console"""
    print(message, flush=True)
    sys.stderr.write(message + '\n')
    sys.stderr.flush()

def test_prints():
    """Test different print methods"""
    print("🧪 TESTING PRINT VISIBILITY")
    print("=" * 50)
    
    # Test 1: Regular print
    print("✅ Test 1: Regular print() - should be visible")
    
    # Test 2: Print with flush
    print("✅ Test 2: print() with flush=True", flush=True)
    
    # Test 3: stderr output
    sys.stderr.write("✅ Test 3: sys.stderr.write() - should be visible\n")
    sys.stderr.flush()
    
    # Test 4: Debug print function
    debug_print("✅ Test 4: debug_print() function - should be visible")
    
    # Test 5: Multiple outputs
    for i in range(3):
        debug_print(f"🔄 Test 5.{i+1}: Multiple debug prints - iteration {i+1}")
    
    print("\n🏁 Print visibility test completed!")
    print("If you can see all the above messages, prints are working correctly.")

if __name__ == "__main__":
    test_prints() 