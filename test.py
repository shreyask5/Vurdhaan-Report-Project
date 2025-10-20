import sys
import os
import pandas as pd
from unittest.mock import patch, MagicMock

# Add the helpers directory to the path so we can import clean.py
sys.path.append(os.path.join(os.path.dirname(__file__), 'helpers'))

from clean import validate_and_correct_icao, safe_load_invalid_icao_codes, safe_write_invalid_icao_codes, extract_airport_data, append_to_csv

def test_validate_and_correct_icao():
    """
    Test the validate_and_correct_icao function with various scenarios
    """
    print("🧪 Testing validate_and_correct_icao function...")
    
    # Test data - sample ICAO codes and their countries
    test_icao_country_dict = {
        'KJFK': 'United States',
        'EGLL': 'United Kingdom', 
        'LFPG': 'France',
        'EDDF': 'Germany',
        'RJTT': 'Japan',
        'YSSY': 'Australia',
        'CYYZ': 'Canada',
        'OMDB': 'United Arab Emirates'
    }
    
    # Test cases
    test_cases = [
        # Test case 1: Valid ICAO code in reference dictionary
        {
            'name': 'Valid ICAO in reference dict',
            'icao_code': 'KJFK',
            'expected_valid': True,
            'expected_country': 'United States',
            'description': 'Should return True and correct country for known ICAO'
        },
        
        # Test case 2: Empty/None ICAO code
        {
            'name': 'Empty ICAO code',
            'icao_code': '',
            'expected_valid': False,
            'expected_country': None,
            'description': 'Should return False for empty ICAO code'
        },
        
        # Test case 3: None ICAO code
        {
            'name': 'None ICAO code',
            'icao_code': None,
            'expected_valid': False,
            'expected_country': None,
            'description': 'Should return False for None ICAO code'
        },
        
        # Test case 4: Invalid ICAO code (not in reference)
        {
            'name': 'Invalid ICAO code',
            'icao_code': 'INVALID',
            'expected_valid': False,
            'expected_country': None,
            'description': 'Should return False for invalid ICAO code'
        },
        
        # Test case 5: Valid ICAO code not in reference (will try online lookup)
        {
            'name': 'Valid ICAO not in reference',
            'icao_code': 'EHAM',  # Amsterdam Airport
            'expected_valid': True,
            'expected_country': 'Netherlands',
            'description': 'Should return True and correct country for valid ICAO not in reference'
        }
    ]
    
    # Run tests
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"   Description: {test_case['description']}")
        print(f"   ICAO Code: {test_case['icao_code']}")
        
        try:
            # Mock the online lookup for specific test cases
            if test_case['icao_code'] == 'EHAM':
                # Mock successful online lookup
                mock_airport_data = {
                    'icao': 'EHAM',
                    'name': 'Amsterdam Airport Schiphol',
                    'latitude': '52.3081',
                    'longitude': '4.7642',
                    'country': 'Netherlands'
                }
                
                with patch('clean.extract_airport_data', return_value=mock_airport_data), \
                     patch('clean.append_to_csv', return_value=True):
                    
                    is_valid, country = validate_and_correct_icao(
                        test_case['icao_code'], 
                        test_icao_country_dict
                    )
            else:
                # Mock failed online lookup for invalid codes
                mock_error_data = {'error': 'No exact matches found', 'icao_code': test_case['icao_code']}
                
                with patch('clean.extract_airport_data', return_value=mock_error_data), \
                     patch('clean.safe_load_invalid_icao_codes', return_value=set()), \
                     patch('clean.safe_write_invalid_icao_codes', return_value=True):
                    
                    is_valid, country = validate_and_correct_icao(
                        test_case['icao_code'], 
                        test_icao_country_dict
                    )
            
            # Check results
            if is_valid == test_case['expected_valid'] and country == test_case['expected_country']:
                print(f"   ✅ PASSED - Valid: {is_valid}, Country: {country}")
                passed_tests += 1
            else:
                print(f"   ❌ FAILED - Expected Valid: {test_case['expected_valid']}, Country: {test_case['expected_country']}")
                print(f"              Got Valid: {is_valid}, Country: {country}")
                
        except Exception as e:
            print(f"   ❌ ERROR - Exception occurred: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"   Passed: {passed_tests}/{total_tests}")
    print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("   🎉 All tests passed!")
    else:
        print("   ⚠️  Some tests failed. Check the output above for details.")
    
    return passed_tests == total_tests

def test_edge_cases():
    """
    Test edge cases and error handling
    """
    print("\n🔍 Testing edge cases...")
    
    test_icao_country_dict = {'KJFK': 'United States'}
    
    edge_cases = [
        # Test with pandas NaN
        {
            'name': 'Pandas NaN',
            'icao_code': pd.NaT,
            'expected_valid': False,
            'expected_country': None
        },
        
        # Test with very long string
        {
            'name': 'Very long string',
            'icao_code': 'A' * 100,
            'expected_valid': False,
            'expected_country': None
        },
        
        # Test with special characters
        {
            'name': 'Special characters',
            'icao_code': 'KJF@',
            'expected_valid': False,
            'expected_country': None
        },
        
        # Test with numbers only
        {
            'name': 'Numbers only',
            'icao_code': '1234',
            'expected_valid': False,
            'expected_country': None
        }
    ]
    
    passed_edge_tests = 0
    
    for i, test_case in enumerate(edge_cases, 1):
        print(f"\n📋 Edge Test {i}: {test_case['name']}")
        print(f"   ICAO Code: {test_case['icao_code']}")
        
        try:
            # Mock failed online lookup
            mock_error_data = {'error': 'Invalid ICAO code', 'icao_code': test_case['icao_code']}
            
            with patch('clean.extract_airport_data', return_value=mock_error_data), \
                 patch('clean.safe_load_invalid_icao_codes', return_value=set()), \
                 patch('clean.safe_write_invalid_icao_codes', return_value=True):
                
                is_valid, country = validate_and_correct_icao(
                    test_case['icao_code'], 
                    test_icao_country_dict
                )
            
            if is_valid == test_case['expected_valid'] and country == test_case['expected_country']:
                print(f"   ✅ PASSED - Valid: {is_valid}, Country: {country}")
                passed_edge_tests += 1
            else:
                print(f"   ❌ FAILED - Expected Valid: {test_case['expected_valid']}, Country: {test_case['expected_country']}")
                print(f"              Got Valid: {is_valid}, Country: {country}")
                
        except Exception as e:
            print(f"   ❌ ERROR - Exception occurred: {str(e)}")
    
    print(f"\n📊 Edge Case Summary:")
    print(f"   Passed: {passed_edge_tests}/{len(edge_cases)}")
    
    return passed_edge_tests == len(edge_cases)

def test_invalid_icao_codes_file():
    """
    Test behavior with invalid ICAO codes file
    """
    print("\n📁 Testing invalid ICAO codes file handling...")
    
    test_icao_country_dict = {'KJFK': 'United States'}
    
    # Test with ICAO code that should be in invalid list
    invalid_icao = 'INVALID123'
    
    try:
        # Mock the invalid ICAO codes file to contain our test code
        with patch('clean.safe_load_invalid_icao_codes', return_value={invalid_icao}):
            is_valid, country = validate_and_correct_icao(invalid_icao, test_icao_country_dict)
            
            if not is_valid and country is None:
                print(f"   ✅ PASSED - Invalid ICAO '{invalid_icao}' correctly rejected from invalid codes file")
                return True
            else:
                print(f"   ❌ FAILED - Expected invalid ICAO to be rejected, got Valid: {is_valid}, Country: {country}")
                return False
                
    except Exception as e:
        print(f"   ❌ ERROR - Exception occurred: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting validate_and_correct_icao function tests...")
    print("=" * 60)
    
    # Run main tests
    main_tests_passed = test_validate_and_correct_icao()
    
    # Run edge case tests
    edge_tests_passed = test_edge_cases()
    
    # Run invalid ICAO codes file test
    invalid_file_test_passed = test_invalid_icao_codes_file()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 FINAL TEST SUMMARY:")
    print(f"   Main Tests: {'✅ PASSED' if main_tests_passed else '❌ FAILED'}")
    print(f"   Edge Cases: {'✅ PASSED' if edge_tests_passed else '❌ FAILED'}")
    print(f"   Invalid File Test: {'✅ PASSED' if invalid_file_test_passed else '❌ FAILED'}")
    
    all_passed = main_tests_passed and edge_tests_passed and invalid_file_test_passed
    print(f"\n   Overall Result: {'🎉 ALL TESTS PASSED!' if all_passed else '⚠️  SOME TESTS FAILED'}")
    
    if not all_passed:
        print("\n💡 Tips for debugging:")
        print("   - Check that all required dependencies are installed")
        print("   - Verify the clean.py module is accessible")
        print("   - Check for any file permission issues with invalid_icao_codes.json")
        print("   - Ensure internet connectivity for online ICAO lookups")