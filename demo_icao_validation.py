#!/usr/bin/env python3
"""
Simple demonstration script for validate_and_correct_icao function
This script shows how to use the function with real examples
"""

import sys
import os

# Add the helpers directory to the path so we can import clean.py
sys.path.append(os.path.join(os.path.dirname(__file__), 'helpers'))

from clean import validate_and_correct_icao

def demo_validate_and_correct_icao():
    """
    Demonstrate the validate_and_correct_icao function with real examples
    """
    print("🔍 Demonstration of validate_and_correct_icao function")
    print("=" * 60)
    
    # Sample ICAO country dictionary (this would typically come from your reference data)
    icao_country_dict = {
        'KJFK': 'United States',      # John F. Kennedy International Airport
        'EGLL': 'United Kingdom',     # London Heathrow Airport
        'LFPG': 'France',            # Paris Charles de Gaulle Airport
        'EDDF': 'Germany',           # Frankfurt Airport
        'RJTT': 'Japan',             # Tokyo Haneda Airport
        'YSSY': 'Australia',         # Sydney Kingsford Smith Airport
        'CYYZ': 'Canada',            # Toronto Pearson International Airport
        'OMDB': 'United Arab Emirates' # Dubai International Airport
    }
    
    # Test cases with different scenarios
    test_cases = [
        'KJFK',      # Valid ICAO in reference dict
        'EGLL',      # Valid ICAO in reference dict
        'EHAM',      # Valid ICAO not in reference (Amsterdam)
        'LHR',       # Invalid ICAO (IATA code instead)
        'INVALID',   # Completely invalid ICAO
        '',          # Empty string
        None,        # None value
        '1234',      # Numbers only
        'KJF@',      # Special characters
    ]
    
    print(f"Testing {len(test_cases)} different ICAO codes...")
    print()
    
    for i, icao_code in enumerate(test_cases, 1):
        print(f"Test {i}: '{icao_code}'")
        
        try:
            is_valid, country = validate_and_correct_icao(icao_code, icao_country_dict)
            
            if is_valid:
                print(f"   ✅ VALID - Country: {country}")
            else:
                print(f"   ❌ INVALID - Country: {country}")
                
        except Exception as e:
            print(f"   ⚠️  ERROR: {str(e)}")
        
        print()
    
    print("=" * 60)
    print("📊 Summary:")
    print("   - Valid ICAO codes return True with the country name")
    print("   - Invalid ICAO codes return False with None")
    print("   - The function checks reference data first, then online sources")
    print("   - Invalid codes are cached to avoid repeated online lookups")
    print("   - The function handles edge cases like empty strings and None values")

if __name__ == "__main__":
    demo_validate_and_correct_icao()
