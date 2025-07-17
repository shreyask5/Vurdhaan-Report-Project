#!/usr/bin/env python3
"""
Test script to demonstrate the error processing functionality.
Creates sample data and processes it to show how the CSV generation works.
"""

import pandas as pd
import json
import os
import tempfile
from helpers.clean import process_error_json_to_csvs

def create_sample_data():
    """Create sample CSV data and JSON error report for testing"""
    
    # Create sample CSV data
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
    
    # Create sample JSON error report
    error_report = {
        "summary": {
            "total_errors": 4,
            "error_rows": 3,
            "categories": {
                "Time": 1,
                "ICAO": 2,
                "Fuel": 1
            }
        },
        "rows_data": {
            "1": {
                "Date": "2024-01-02",
                "A/C Registration": "ABC123",
                "Flight": "FL002",
                "Origin ICAO": "KLAX",
                "Destination ICAO": "KJFK",
                "ATD (UTC) Block out": "08:45",
                "ATA (UTC) Block in": "12:30",
                "Uplift Volume": 1200.0,
                "Uplift Density": 0.8,
                "Uplift weight": 960.0,
                "Remaining Fuel From Prev. Flight": 150.0,
                "Block off Fuel": 1110.0,
                "Block on Fuel": 250.0,
                "A/C Type": "B737",
                "Fuel Type": "Jet-A1"
            },
            "2": {
                "Date": "2024-01-03",
                "A/C Registration": "DEF456",
                "Flight": "FL003",
                "Origin ICAO": "EGLL",
                "Destination ICAO": "LFPG",
                "ATD (UTC) Block out": "12:15",
                "ATA (UTC) Block in": "15:30",
                "Uplift Volume": 800.0,
                "Uplift Density": 0.8,
                "Uplift weight": 640.0,
                "Remaining Fuel From Prev. Flight": 300.0,
                "Block off Fuel": 940.0,
                "Block on Fuel": 400.0,
                "A/C Type": "A320",
                "Fuel Type": "Jet-A1"
            },
            "4": {
                "Date": "2024-01-05",
                "A/C Registration": "GHI789",
                "Flight": "FL005",
                "Origin ICAO": "EDDF",
                "Destination ICAO": "KJFK",
                "ATD (UTC) Block out": "10:00",
                "ATA (UTC) Block in": "15:15",
                "Uplift Volume": 1100.0,
                "Uplift Density": 0.8,
                "Uplift weight": 880.0,
                "Remaining Fuel From Prev. Flight": 180.0,
                "Block off Fuel": 1060.0,
                "Block on Fuel": 280.0,
                "A/C Type": "B777",
                "Fuel Type": "Jet-A1"
            }
        },
        "categories": [
            {
                "name": "Time",
                "errors": [
                    {
                        "reason": "Invalid time format",
                        "rows": [
                            {
                                "row_idx": 1,
                                "cell_data": "08:45",
                                "columns": ["ATD (UTC) Block out"]
                            }
                        ]
                    }
                ]
            },
            {
                "name": "ICAO",
                "errors": [
                    {
                        "reason": "Invalid ICAO code",
                        "rows": [
                            {
                                "row_idx": 2,
                                "cell_data": "EGLL",
                                "columns": ["Origin ICAO"]
                            },
                            {
                                "row_idx": 4,
                                "cell_data": "EDDF",
                                "columns": ["Origin ICAO"]
                            }
                        ]
                    }
                ]
            },
            {
                "name": "Fuel",
                "errors": [
                    {
                        "reason": "Fuel calculation mismatch",
                        "rows": [
                            {
                                "row_idx": 2,
                                "cell_data": "Volume: 800, Density: 0.8, Weight: 640",
                                "columns": ["Uplift Volume", "Uplift Density", "Uplift weight"]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    return df, error_report

def main():
    """Test the error processing functionality"""
    
    print("🧪 Testing Error Processing Functionality")
    print("=" * 50)
    
    # Create sample data
    sample_df, sample_error_report = create_sample_data()
    
    print(f"📊 Created sample data with {len(sample_df)} rows")
    print(f"❌ Sample error report contains {sample_error_report['summary']['total_errors']} errors affecting {sample_error_report['summary']['error_rows']} rows")
    print()
    
    # Create temporary files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save sample CSV
        csv_path = os.path.join(temp_dir, 'sample_data.csv')
        sample_df.to_csv(csv_path, index=False)
        
        # Save sample JSON error report
        json_path = os.path.join(temp_dir, 'error_report.json')
        with open(json_path, 'w') as f:
            json.dump(sample_error_report, f, indent=2)
        
        print(f"💾 Saved test files to: {temp_dir}")
        print(f"  📄 CSV: {os.path.basename(csv_path)}")
        print(f"  📋 JSON: {os.path.basename(json_path)}")
        print()
        
        # Process the files
        print("🔄 Processing files...")
        clean_csv_path, errors_csv_path = process_error_json_to_csvs(
            json_path, sample_df, temp_dir
        )
        
        if clean_csv_path and errors_csv_path:
            print("\n✅ Success! Files generated:")
            print(f"  🧹 Clean data CSV: {os.path.basename(clean_csv_path)}")
            print(f"  ⚠️  Errors data CSV: {os.path.basename(errors_csv_path)}")
            
            # Load and display the results
            clean_df = pd.read_csv(clean_csv_path)
            errors_df = pd.read_csv(errors_csv_path)
            
            print(f"\n📊 Results Summary:")
            print(f"  Original data: {len(sample_df)} rows")
            print(f"  Clean data: {len(clean_df)} rows")
            print(f"  Error data: {len(errors_df)} rows")
            
            print(f"\n🧹 Clean Data Sample (first 3 rows):")
            print(clean_df.head(3).to_string(index=False))
            
            print(f"\n⚠️  Error Data Sample (first 3 rows):")
            print(errors_df[['Error_Category', 'Error_Reason', 'Row_Index', 'Flight', 'Origin ICAO']].head(3).to_string(index=False))
            
            # Copy files to current directory for inspection
            import shutil
            final_clean_path = 'sample_clean_data.csv'
            final_errors_path = 'sample_errors_data.csv'
            
            shutil.copy2(clean_csv_path, final_clean_path)
            shutil.copy2(errors_csv_path, final_errors_path)
            
            print(f"\n📁 Files copied to current directory:")
            print(f"  {final_clean_path}")
            print(f"  {final_errors_path}")
            
        else:
            print("\n❌ Failed to process files")

if __name__ == "__main__":
    main() 