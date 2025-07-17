#!/usr/bin/env python3
"""
Test script to verify that generate_error_report automatically creates CSV files.
"""

import pandas as pd
import os
import tempfile
import shutil
from helpers.clean import generate_error_report, mark_error, error_tracker, error_rows

def test_auto_csv_generation():
    """Test that generate_error_report automatically creates clean_data.csv and errors_data.csv"""
    
    print("🧪 Testing Automatic CSV Generation")
    print("=" * 50)
    
    # Create sample data
    sample_data = {
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
        'A/C Registration': ['ABC123', 'ABC123', 'DEF456', 'DEF456', 'GHI789'],
        'Flight': ['FL001', 'FL002', 'FL003', 'FL004', 'FL005'],
        'Origin ICAO': ['KJFK', 'KLAX', 'EGLL', 'LFPG', 'EDDF'],
        'Destination ICAO': ['KLAX', 'KJFK', 'LFPG', 'EGLL', 'KJFK'],
        'ATD (UTC) Block out': ['14:30', '08:45', '12:15', '16:20', '10:00'],
        'ATA (UTC) Block in': ['18:45', '12:30', '15:30', '19:45', '15:15'],
        'Uplift Volume': [1000, 1200, 800, 950, 1100],
        'Uplift Density': [0.8, 0.8, 0.8, 0.8, 0.8],
        'Uplift weight': [800, 960, 640, 760, 880],
        'Remaining Fuel From Prev. Flight': [200, 150, 300, 250, 180],
        'Block off Fuel': [1000, 1110, 940, 1010, 1060],
        'Block on Fuel': [300, 250, 400, 350, 280],
        'A/C Type': ['B737', 'B737', 'A320', 'A320', 'B777'],
        'Fuel Type': ['Jet-A1', 'Jet-A1', 'Jet-A1', 'Jet-A1', 'Jet-A1']
    }
    
    df = pd.DataFrame(sample_data)
    print(f"📊 Created sample data with {len(df)} rows")
    
    # Clear any existing errors
    global error_tracker, error_rows
    from helpers.clean import error_categories
    error_tracker = {category: [] for category in error_categories}
    error_rows = set()
    
    # Create some sample errors
    mark_error("08:45", "Invalid time format", 1, "Time", "ATD (UTC) Block out")
    mark_error("EGLL", "Invalid ICAO code", 2, "ICAO", "Origin ICAO")
    mark_error("EDDF", "Invalid ICAO code", 4, "ICAO", "Origin ICAO")
    mark_error("Volume: 800, Density: 0.8, Weight: 640", "Fuel calculation mismatch", 2, "Fuel", ["Uplift Volume", "Uplift Density", "Uplift weight"])
    
    print(f"❌ Created 4 sample errors affecting 3 rows")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"💾 Using temp directory: {temp_dir}")
        
        # Call generate_error_report (this should auto-generate CSV files)
        print("\n🔄 Calling generate_error_report...")
        json_file = generate_error_report(df, temp_dir)
        
        if json_file:
            print(f"✅ JSON report created: {os.path.basename(json_file)}")
            
            # Check if CSV files were automatically created
            clean_csv = os.path.join(temp_dir, 'clean_data.csv')
            errors_csv = os.path.join(temp_dir, 'errors_data.csv')
            
            print(f"\n🔍 Checking for auto-generated CSV files:")
            print(f"  Clean CSV exists: {os.path.exists(clean_csv)}")
            print(f"  Errors CSV exists: {os.path.exists(errors_csv)}")
            
            if os.path.exists(clean_csv) and os.path.exists(errors_csv):
                # Load and analyze the results
                clean_df = pd.read_csv(clean_csv)
                errors_df = pd.read_csv(errors_csv)
                
                print(f"\n📊 Results Summary:")
                print(f"  Original data: {len(df)} rows")
                print(f"  Clean data: {len(clean_df)} rows")
                print(f"  Error data: {len(errors_df)} rows")
                
                # Verify the results
                expected_clean_rows = 2  # Rows 0 and 3 should be clean (rows 1, 2, 4 have errors)
                expected_error_rows = 4  # 4 total error entries (row 2 appears twice)
                
                print(f"\n✅ Verification:")
                print(f"  Expected clean rows: {expected_clean_rows}, Actual: {len(clean_df)} {'✓' if len(clean_df) == expected_clean_rows else '✗'}")
                print(f"  Expected error entries: {expected_error_rows}, Actual: {len(errors_df)} {'✓' if len(errors_df) == expected_error_rows else '✗'}")
                
                # Show sample data
                print(f"\n🧹 Clean Data (should be rows 0 and 3):")
                print(clean_df[['Flight', 'Origin ICAO', 'Destination ICAO']].to_string(index=False))
                
                print(f"\n⚠️  Error Data Sample:")
                print(errors_df[['Error_Category', 'Error_Reason', 'Row_Index', 'Flight']].to_string(index=False))
                
                # Copy files to current directory for inspection
                final_clean_path = 'auto_generated_clean_data.csv'
                final_errors_path = 'auto_generated_errors_data.csv'
                
                shutil.copy2(clean_csv, final_clean_path)
                shutil.copy2(errors_csv, final_errors_path)
                
                print(f"\n📁 Files copied to current directory for inspection:")
                print(f"  {final_clean_path}")
                print(f"  {final_errors_path}")
                
                return True
            else:
                print("\n❌ CSV files were not auto-generated")
                return False
        else:
            print("\n❌ Failed to create JSON report")
            return False

if __name__ == "__main__":
    success = test_auto_csv_generation()
    if success:
        print("\n🎉 Auto CSV generation test PASSED!")
    else:
        print("\n💥 Auto CSV generation test FAILED!") 