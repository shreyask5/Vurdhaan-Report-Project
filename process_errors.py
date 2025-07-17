#!/usr/bin/env python3
"""
Script to process JSON error reports and generate clean and errors CSV files.

Usage:
    python process_errors.py <json_file_path> <original_csv_path> [output_directory]

Example:
    python process_errors.py uploads/abc123/error_report.json uploads/abc123/original.csv outputs/
"""

import sys
import os
from helpers.clean import generate_csvs_from_json_report

def main():
    if len(sys.argv) < 3:
        print("Usage: python process_errors.py <json_file_path> <original_csv_path> [output_directory]")
        print("\nExample:")
        print("  python process_errors.py uploads/abc123/error_report.json uploads/abc123/original.csv outputs/")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    original_csv_path = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Validate input files exist
    if not os.path.exists(json_file_path):
        print(f"Error: JSON file not found: {json_file_path}")
        sys.exit(1)
    
    if not os.path.exists(original_csv_path):
        print(f"Error: Original CSV file not found: {original_csv_path}")
        sys.exit(1)
    
    print(f"Processing error report...")
    print(f"  JSON file: {json_file_path}")
    print(f"  Original CSV: {original_csv_path}")
    print(f"  Output directory: {output_dir or os.path.dirname(json_file_path)}")
    print()
    
    # Process the files
    clean_csv_path, errors_csv_path = generate_csvs_from_json_report(
        json_file_path=json_file_path,
        original_csv_path=original_csv_path,
        output_dir=output_dir
    )
    
    if clean_csv_path and errors_csv_path:
        print("\n✅ Success! Files generated:")
        print(f"  Clean data CSV: {clean_csv_path}")
        print(f"  Errors data CSV: {errors_csv_path}")
    else:
        print("\n❌ Failed to process files. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 