import json
import os
import requests
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd
from datetime import datetime
import chardet
import csv
import xlwings as xw
from lzstring import LZString
from collections import defaultdict
from helpers.corsia import filter_reportable_flights

# Load environment variables for OpenAI
try:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            openai_client = OpenAI(api_key=api_key)
        except TypeError as e:
            # Handle version compatibility issues
            print(f"Warning: OpenAI client initialization failed: {e}")
            openai_client = None
    else:
        openai_client = None
except ImportError:
    openai_client = None
    print("Warning: dotenv or openai package not found. LLM validation will be skipped.")

def process_corsia_error(error_string):
    """
    Uses OpenAI to process CORSIA related errors and get correct country information
    
    Args:
        error_string (str): The error string containing the ICAO code or country name
        
    Returns:
        list: [is_confident, icao_member_state, alternative_member_state_name]
    """
    if not openai_client:
        return [False, "", ""]
    
    # Define function schema for OpenAI - simplified version
    function_schema = {
        "type": "web_search_preview",
        "type": "function",
        "function": {
            "name": "parse_corsia_error",
            "description": "Map country names or codes to official ICAO member states",
            "parameters": {
                "type": "object",
                "properties": {
                    "is_confident": {
                        "type": "boolean"
                    },
                    "ICAO_member_state": {
                        "type": "string"
                    },
                    "alternative_member_state_name": {
                        "type": "string"
                    }
                },
                "required": ["is_confident", "ICAO_member_state", "alternative_member_state_name"]
            }
        }
    }

    # Simplified system instructions
    system_instructions = "Identify the official ICAO member state name from the error string. If an alternative name is mentioned, provide the official name and the alternative name. Be confident when you're sure of the mapping."
    
    try:
        # Create a direct user message with the original error string and the full list of ICAO states
        user_content = f"The error string is: {error_string}\n\n"
        user_content += "Here are the official ICAO Member States: Afghanistan, Albania, Algeria, Andorra, Angola, Antigua and Barbuda, Argentina, Armenia, Australia, Austria, Azerbaijan, Bahamas, Bahrain, Bangladesh, Barbados, Belarus, Belgium, Belize, Benin, Bhutan, Bolivia (Plurinational State of), Bosnia and Herzegovina, Botswana, Brazil, Brunei Darussalam, Bulgaria, Burkina Faso, Burundi, Cabo Verde, Cambodia, Cameroon, Canada, Central African Republic, Chad, Chile, China, Colombia, Comoros, Congo, Cook Islands, Costa Rica, Côte d'Ivoire, Croatia, Cuba, Cyprus, Czechia, Democratic People's Republic of Korea, Democratic Republic of the Congo, Denmark, Djibouti, Dominica, Dominican Republic, Ecuador, Egypt, El Salvador, Equatorial Guinea, Eritrea, Estonia, Eswatini, Ethiopia, Fiji, Finland, France, Gabon, Gambia, Georgia, Germany, Ghana, Greece, Grenada, Guatemala, Guinea, Guinea-Bissau, Guyana, Haiti, Honduras, Hungary, Iceland, India, Indonesia, Iran (Islamic Republic of), Iraq, Ireland, Israel, Italy, Jamaica, Japan, Jordan, Kazakhstan, Kenya, Kiribati, Kuwait, Kyrgyzstan, Lao People's Democratic Republic, Latvia, Lebanon, Lesotho, Liberia, Libya, Lithuania, Luxembourg, Madagascar, Malawi, Malaysia, Maldives, Mali, Malta, Marshall Islands, Mauritania, Mauritius, Mexico, Micronesia (Federated States of), Monaco, Mongolia, Montenegro, Morocco, Mozambique, Myanmar, Namibia, Nauru, Nepal, Netherlands, New Zealand, Nicaragua, Niger, Nigeria, North Macedonia, Norway, Oman, Pakistan, Palau, Panama, Papua New Guinea, Paraguay, Peru, Philippines, Poland, Portugal, Qatar, Republic of Korea, Republic of Moldova, Romania, Russian Federation, Rwanda, Saint Kitts and Nevis, Saint Lucia, Saint Vincent and the Grenadines, Samoa, San Marino, Sao Tome and Principe, Saudi Arabia, Senegal, Serbia, Seychelles, Sierra Leone, Singapore, Slovakia, Slovenia, Solomon Islands, Somalia, South Africa, South Sudan, Spain, Sri Lanka, Sudan, Suriname, Sweden, Switzerland, Syrian Arab Republic, Tajikistan, Thailand, Timor-Leste, Togo, Tonga, Trinidad and Tobago, Tunisia, Türkiye, Turkmenistan, Tuvalu, Uganda, Ukraine, United Arab Emirates, United Kingdom, United Republic of Tanzania, United States, Uruguay, Uzbekistan, Vanuatu, Venezuela (Bolivarian Republic of), Viet Nam, Yemen, Zambia, Zimbabwe"
        user_content += "\n\nRemember common alternative names: Turkey → Türkiye, Burma → Myanmar, Czech Republic → Czechia, etc."

        # Make a request with function calling
        response = openai_client.chat.completions.create(
            model="o4-mini",
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_content}
            ],
            tools=[function_schema],
            tool_choice={"type": "function", "function": {"name": "parse_corsia_error"}}
        )

        # Extract the structured response
        function_call = response.choices[0].message.tool_calls[0]
        function_args = json.loads(function_call.function.arguments)
        
        # Return the relevant parts
        return [
            function_args["is_confident"], 
            function_args["ICAO_member_state"], 
            function_args["alternative_member_state_name"]
        ]
    except Exception as e:
        print(f"Error processing CORSIA error with OpenAI: {str(e)}")
        return [False, "", ""]

def append_to_csv(data, csv_path):
    """
    Append the extracted airport data to the specified CSV file
    
    Args:
        data (dict): Dictionary containing airport data
        csv_path (str): Path to the CSV file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        
        # Check if file exists to determine if we need to write headers
        file_exists = os.path.isfile(csv_path)
        
        # Prepare the row data in the required format
        row = [
            data["icao"],
            data["name"],
            data["latitude"],
            data["longitude"],
            "",  # Terr_code (left blank as specified)
            data["country"],
            data["icao"]
        ]
        
        # Open the file in append mode
        with open(csv_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write headers if the file doesn't exist
            if not file_exists:
                writer.writerow(["ICAO_Code", "Location_Name", "Latitude", "Longitude", "Terr_code", "ICAO Member State", "ICAO_Code"])
            
            # Write the data row
            writer.writerow(row)
        
        return True
    
    except Exception as e:
        print(f"Error appending to CSV: {str(e)}")
        return False



def load_icao_common_names():
    """
    Load the ICAO common names JSON file
    
    Returns:
        dict: Dictionary mapping official names to lists of common names
    """
    common_names_dict = {}
    common_names_file = "icao_countries_common_names.json"
    
    # Create the file if it doesn't exist
    if not os.path.exists(common_names_file):
        try:
            os.makedirs(os.path.dirname(common_names_file), exist_ok=True)
            with open(common_names_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=2)
            print(f"Created new ICAO common names file: {common_names_file}")
        except Exception as e:
            print(f"Failed to create ICAO common names file: {str(e)}")
            return {}
    
    # Load the file
    try:
        with open(common_names_file, 'r', encoding='utf-8') as f:
            common_names_dict = json.load(f)
    except Exception as e:
        print(f"Error loading ICAO common names: {str(e)}")
    
    return common_names_dict

def save_icao_common_names(common_names_dict):
    """
    Save the updated ICAO common names to JSON
    
    Args:
        common_names_dict (dict): Dictionary of official names to lists of common names
    """
    common_names_file = "icao_countries_common_names.json"
    
    try:
        with open(common_names_file, 'w', encoding='utf-8') as f:
            json.dump(common_names_dict, f, indent=2)
    except Exception as e:
        print(f"Error saving ICAO common names: {str(e)}")

def find_official_name_by_common_name(row_country):
    """
    Search for a country's official name using its common name
    
    Args:
        row_country (str): The common country name to search for
        
    Returns:
        str or None: The official country name if found, None otherwise
    """
    common_names_dict = load_icao_common_names()
    
    # First check if row_country is already an official name
    if row_country in common_names_dict:
        return row_country
    
    # Then search through all common names lists
    for official_name, common_names in common_names_dict.items():
        if row_country in common_names:
            return official_name
    
    # If not found, return None
    return None

def verify_and_correct_country_name(row_country, expected_country=None, icao_code=None):
    """
    Verify and correct country name mismatches
    
    Args:
        row_country (str): The country name from the row
        expected_country (str): The expected country name from the reference
        icao_code (str, optional): The ICAO code if available
        
    Returns:
        tuple: (corrected_country, was_corrected, error_message)
    """
    if row_country == expected_country:
        return row_country, False, None
    
    # Load common names dictionary
    common_names_dict = load_icao_common_names()
    
    # Check if the expected country has any common names
    common_names = common_names_dict.get(expected_country, [])
    
    # Check if row_country is in the common names list
    if row_country in common_names:
        return expected_country, True, None
    
    # If we have an ICAO code, try to get more information using LLM
    if icao_code and expected_country:
        error_string = f"{icao_code} : Country mismatch (expected {expected_country}, got {row_country})"
        llm_result = process_corsia_error(error_string)
        print(f"\n\n\n\n\n error string : {error_string} \n\n result: {llm_result} \n\n common names : {common_names}\n\n\n\n\n")
        
        is_confident = llm_result[0]
        icao_member_state = llm_result[1]
        alternative_name = llm_result[2]
        
        # If LLM is confident and provided an official name
        if is_confident and icao_member_state:
            # Update common names dictionary with the new alternative name if it's not empty
            if alternative_name and row_country not in common_names:
                if expected_country in common_names_dict:
                    common_names_dict[expected_country].append(row_country)
                else:
                    common_names_dict[expected_country] = [row_country]
                
                # Save the updated dictionary
                save_icao_common_names(common_names_dict)
                
            return expected_country, True, None
    
    if expected_country:
        error_string = f"Country mismatch (expected {expected_country}, got {row_country})"
        llm_result = process_corsia_error(error_string)
        print(f"\n\n\n\n\n error string : {error_string} \n\n result: {llm_result} \n\n\n\n\n")
        
        is_confident = llm_result[0]
        icao_member_state = llm_result[1]
        alternative_name = llm_result[2]
        
        # If LLM is confident and provided an official name
        if is_confident and icao_member_state:
            # Update common names dictionary with the new alternative name if it's not empty
            if alternative_name and row_country not in common_names:
                if expected_country in common_names_dict:
                    common_names_dict[expected_country].append(row_country)
                else:
                    common_names_dict[expected_country] = [row_country]
                
                # Save the updated dictionary
                save_icao_common_names(common_names_dict)
                
            return expected_country, True, None
    
    # Search the whole file using the row_country in the json file
    official_name = find_official_name_by_common_name(row_country)
    
    # If found, return the official name
    if official_name:
        return official_name, True, None
    
    # If not found, send the data to the LLM
    error_string = f"Return official icao member state country by using the common name country : {row_country}"
    llm_result = process_corsia_error(error_string)
    
    is_confident = llm_result[0]
    icao_member_state = llm_result[1]
    alternative_name = llm_result[2]
    
    # If LLM is confident and provided an official name
    if is_confident and icao_member_state:
        # Add the new mapping to the common names dictionary
        if icao_member_state in common_names_dict:
            if row_country not in common_names_dict[icao_member_state]:
                common_names_dict[icao_member_state].append(row_country)
        else:
            common_names_dict[icao_member_state] = [row_country]
        
        # Save the updated dictionary
        save_icao_common_names(common_names_dict)
        
        return icao_member_state, True, None
    
    # If we couldn't correct the country name
    error_msg = f"Country mismatch (expected {expected_country})"
    return row_country, False, error_msg

def extract_airport_data(icao_code):
    """
    Extract airport data from gcmap.com for a given ICAO code
    
    Args:
        icao_code (str): The ICAO code of the airport
        
    Returns:
        dict: Dictionary containing the extracted information or error message
    """
    url = f"http://www.gcmap.com/airport/{icao_code}"
    
    try:
        # Send HTTP request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if "No exact matches" is present
        if "No exact matches" in response.text:
            return {"error": f"No exact matches found for the provided ICAO code: {icao_code}","icao_code":icao_code}

        # Extract data using table rows
        airport_data = {}
        
        # Find all table rows
        rows = soup.find_all('tr')
        
        # Extract data from rows
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                header = cells[0].text.strip()
                
                if header == "Name:":
                    airport_data["name"] = cells[1].text.strip()
                elif header == "ICAO:":
                    icao_cell = cells[1]
                    if icao_cell.find('a'):
                        airport_data["icao"] = icao_cell.find('a').text.strip()
                    else:
                        airport_data["icao"] = icao_cell.text.strip()
                elif header == "Latitude:":
                    # Extract the numeric value from the abbr tag
                    lat_cell = cells[1]
                    lat_abbr = lat_cell.find('abbr', class_="latitude")
                    if lat_abbr and lat_abbr.has_attr('title'):
                        airport_data["latitude"] = lat_abbr['title']
                    else:
                        # Fallback to parsing the text if abbr is not found
                        lat_text = lat_cell.text.strip()
                        lat_match = re.search(r"\((\d+\.\d+)\)", lat_text)
                        if lat_match:
                            airport_data["latitude"] = lat_match.group(1)
                        else:
                            airport_data["latitude"] = lat_text
                elif header == "Longitude:":
                    # Extract the numeric value from the abbr tag
                    lon_cell = cells[1]
                    lon_abbr = lon_cell.find('abbr', class_="longitude")
                    if lon_abbr and lon_abbr.has_attr('title'):
                        airport_data["longitude"] = lon_abbr['title']
                    else:
                        # Fallback to parsing the text if abbr is not found
                        lon_text = lon_cell.text.strip()
                        lon_match = re.search(r"\((\d+\.\d+)\)", lon_text)
                        if lon_match:
                            airport_data["longitude"] = lon_match.group(1)
                        else:
                            airport_data["longitude"] = lon_text
        
        # Extract country from the span with class "country-name"
        country_element = soup.find('span', class_='country-name')
        if country_element:
            airport_data["country"] = country_element.text.strip()
        else:
            # Fallback method: try to find it by looking for "City:" row
            city_row = soup.find('td', text='City:')
            if city_row and city_row.find_next_sibling('td'):
                city_cell = city_row.find_next_sibling('td')
                country_span = city_cell.find('span', class_='country-name')
                if country_span:
                    airport_data["country"] = country_span.text.strip()
                else:
                    # Last resort: try to parse from the city cell text
                    city_text = city_cell.text.strip()
                    if ',' in city_text:
                        airport_data["country"] = city_text.split(',')[-1].strip()
                    else:
                        airport_data["country"] = "Country not found"
            else:
                airport_data["country"] = "Country not found"
        
        # Validate if we have all necessary data
        required_fields = ["name", "icao", "latitude", "longitude", "country"]
        missing_fields = [field for field in required_fields if field not in airport_data]
        
        if missing_fields:
            return {"error": f"Missing fields: {', '.join(missing_fields)}"}
        print(airport_data)
        corrected_country, was_corrected, error_msg = verify_and_correct_country_name(
            airport_data["country"],None,airport_data["icao"]
        )

        if was_corrected:
             airport_data["country"] = corrected_country
             print("Corrected")
        else:
            print("Not corrected")
            return {"error": f"Missing fields: Country {error_msg}"}

        print(airport_data)
        return airport_data
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Error making request: {str(e)}","icao_code":icao_code}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}","icao_code":icao_code}


def validate_and_correct_icao(icao_code,icao_country_dict):
    """
    Validate and correct an ICAO code
    
    Args:
        icao_code (str): The ICAO code to validate
        
    Returns:
        tuple: (is_valid, country_name)
    """
    if not icao_code or pd.isna(icao_code):
        return False, None
    
    # Check if the ICAO code is in the invalid_icao_codes.json file
    invalid_icao_file = "invalid_icao_codes.json"
    invalid_icao_codes = set()
    if os.path.exists(invalid_icao_file):
        try:
            with open(invalid_icao_file, 'r', encoding='utf-8') as f:
                invalid_icao_codes = set(json.load(f))
        except Exception:
            invalid_icao_codes = set()
    
    if icao_code in invalid_icao_codes:
        return False, None
    
    # First check if it's in the reference dataset
    if icao_code in icao_country_dict:
        return True, icao_country_dict[icao_code]
    
    # If not in reference, try to get it from online source
    airport_data = extract_airport_data(icao_code)
    if "error" in airport_data:
        # Add the invalid ICAO code to the file
        try:
            # Always reload to avoid race conditions
            if os.path.exists(invalid_icao_file):
                with open(invalid_icao_file, 'r', encoding='utf-8') as f:
                    invalid_icao_codes = set(json.load(f))
            else:
                invalid_icao_codes = set()
            # Append the code if not already present
            if "icao_code" in airport_data:
                code_to_add = airport_data["icao_code"]
            elif "icao" in airport_data:
                code_to_add = airport_data["icao"]
            else:
                code_to_add = icao_code
            if code_to_add not in invalid_icao_codes:
                invalid_icao_codes.add(code_to_add)
                with open(invalid_icao_file, 'w', encoding='utf-8') as f:
                    json.dump(sorted(list(invalid_icao_codes)), f, indent=2)
        except Exception as e:
            print(f"Error updating invalid_icao_codes.json: {e}")
        return False, None
    
    if "error" not in airport_data and "country" in airport_data:
        csv_path = "airports.csv"
        cwd = os.getcwd()
        full_path = os.path.join(cwd, csv_path)
        if append_to_csv(airport_data, full_path):
            print(f"\nSuccessfully appended data to {full_path}")
        else:
            print(f"\nFailed to append data to {full_path}")
        
        return True, airport_data["country"]
    
    return False, None















# Define a structured array of dictionaries for different error categories
error_categories = ["Time", "Date", "Fuel", "ICAO", "Sequence", "Missing","Column Missing", "Sequence"]
error_tracker = {category: [] for category in error_categories}

# Track all rows with errors
error_rows = set()  # Using a set for faster lookup


















def mark_error(cell_data, reason, row_idx=None, category="Missing", column=None):
    """
    Mark a cell as having an error and add it to the appropriate error category dictionary.
    
    Parameters:
    - cell_data: The actual value in the cell
    - reason: Why it's considered an error
    - row_idx: The row index in the dataframe
    - category: Error category (Time, Date, Fuel, ICAO, Sequence, Missing)
    - column: The column name where the error was found
    """
    # Validate category
    if category not in error_categories:
        category = "Missing"  # Default category if invalid
    
    # Create error entry
    error_entry = {
        "row_idx": row_idx,
        "reason": reason,
        "cell_data": cell_data,
        "columns": [column] if column else []
    }
    
    # Add to the appropriate category
    error_tracker[category].append(error_entry)
    
    # Track the row index in error_rows set
    if row_idx is not None:
        error_rows.add(row_idx)
            
    return f"Error: {cell_data} : {reason}"

def validate_and_process_file(file_path, result_df, ref_df, date_format="DMY", flight_starts_with="", start_date=None, end_date=None, fuel_method="Block Off - Block On",scheme=None):
    """
    Validates and processes the CSV file, checking for all required columns and data quality.

    Parameters:
    - file_path: Path to the original CSV file
    - result_df: DataFrame to validate
    - ref_df: Reference DataFrame for ICAO code validation
    - date_format: Format for date validation (DMY or MDY)
    - flight_starts_with: Expected prefix for Flight numbers
    - start_date: Minimum allowed date
    - end_date: Maximum allowed date
    - fuel_method: Fuel calculation method ('Block Off - Block On' or 'Method B')
    - scheme

    Returns:
    - is_valid: Boolean indicating if the file is valid
    - output_path: Path to the processed file (empty string if validation failed)
    - result_df: DataFrame to validate
    - output_path_json: Path to the saved JSON file
    """

    #Folder path file
    folder_path = os.path.dirname(file_path)

    # Define all required columns (non-fuel columns that are always required)
    required_columns = [
        'Origin ICAO',
        'Destination ICAO',
        'ATD (UTC) Block Off',
        'ATA (UTC) Block On',
        'Date',
        'A/C Registration',
        'Flight No',
        'A/C Type',
        'Fuel Consumption'
        # 'Fuel Type'  # REMOVED: Fuel Type column has been removed from requirements
    ]

    # Define fuel-specific required columns based on method
    print("fuel_method: ", fuel_method)
    if fuel_method == 'Block Off - Block On':
        required_fuel_columns = ['Block Off Fuel', 'Block On Fuel']
    elif fuel_method == 'Method B':
        required_fuel_columns = ['Uplift weight', 'Remaining Fuel From Prev. Flight', 'Block On Fuel']
    else:
        # Fallback: require all fuel columns
        required_fuel_columns = [
            'Uplift Volume', 'Uplift Density', 'Uplift weight',
            'Remaining Fuel From Prev. Flight', 'Block Off Fuel', 'Block On Fuel'
        ]

    # Combine required columns
    all_required_columns = required_columns + required_fuel_columns



    
    """
    Checks if the flight sequence for each aircraft is valid:
    Destination ICAO of one flight should match Origin ICAO of next flight.
    Ignores rows with date or time errors for sequence validation.
    
    Parameters:
    - result_df: DataFrame with flight data
    - mark_error: Function to mark errors in the error tracker
    """
    print("Checking flight sequence...")
    
    # Collect row indices that have Date or Time errors (to exclude from sequence validation)
    date_time_error_rows = set()
    
    # Get Date error rows
    for error in error_tracker.get("Date", []):
        if error["row_idx"] is not None:
            date_time_error_rows.add(int(error["row_idx"]))
    
    # Get Time error rows
    for error in error_tracker.get("Time", []):
        if error["row_idx"] is not None:
            date_time_error_rows.add(int(error["row_idx"]))
    
    print(f"Excluding {len(date_time_error_rows)} rows with date/time errors from sequence validation")

    # Group by aircraft registration
    for ac_reg, group in result_df.groupby('A/C Registration'):
        # Note: group already has 'index' column with original indices from earlier reset_index()
        
        # Filter out rows with date/time errors for sequence validation
        # Keep track of original positions for error marking
        valid_flights = []
        original_positions = []
        
        for i, (pandas_idx, row) in enumerate(group.iterrows()):
            original_idx = int(row['index'])
            if original_idx not in date_time_error_rows:
                valid_flights.append(row)
                original_positions.append(i)  # Store original position in the group
        
        # Skip sequence validation if less than 2 valid flights
        if len(valid_flights) < 2:
            continue
        
        # Iterate through valid flights in sequence (excluding the last one)
        for i in range(len(valid_flights) - 1):
            current_flight = valid_flights[i]
            next_flight = valid_flights[i + 1]
            
            # Get original dataframe indices for these rows (ensure they're integers)
            current_idx = int(current_flight['index'])
            next_idx = int(next_flight['index'])
            
            # Check if Destination ICAO of current flight matches Origin ICAO of next flight
            if current_flight['Destination ICAO'] != next_flight['Origin ICAO']:
                # Get sequence break details
                dest_icao = current_flight['Destination ICAO']
                next_origin_icao = next_flight['Origin ICAO']
                
                # Create error message
                error_msg = f"{ac_reg}: Sequence Failed for Destination ICAO: {dest_icao} to Origin ICAO: {next_origin_icao}"
                
                # Mark error for flight before the current flight (if exists)
                if i > 0:
                    prev_flight = valid_flights[i - 1]
                    prev_idx = int(prev_flight['index'])
                    mark_error(
                        f"{ac_reg} : {dest_icao} → {next_origin_icao}",
                        error_msg,
                        prev_idx,
                        "Sequence",
                        ["Origin ICAO", "Destination ICAO"]
                    )

                # Mark errors for current flight and next flight
                mark_error(
                    f"{ac_reg} : {dest_icao} → {next_origin_icao}",
                    error_msg,
                    current_idx,
                    "Sequence",
                    ["Origin ICAO", "Destination ICAO"]
                )
                
                mark_error(
                    f"{ac_reg} : {dest_icao} → {next_origin_icao}",
                    error_msg,
                    next_idx,
                    "Sequence",
                    ["Origin ICAO", "Destination ICAO"]
                )
                 
                # Mark error for flight after the next flight (if exists)
                if i + 2 < len(valid_flights):
                    after_next_flight = valid_flights[i + 2]
                    after_next_idx = int(after_next_flight['index'])
                    mark_error(
                        f"{ac_reg} : {dest_icao} → {next_origin_icao}",
                        error_msg,
                        after_next_idx,
                        "Sequence",
                        ["Origin ICAO", "Destination ICAO"]
                    )



    # FILTER REPORTABLE FLIGHTS
    # Apply flight prefix filtering to remove non-reportable flights
    # This must be done before other validations to ensure only reportable flights are checked
    if flight_starts_with:
        result_df = filter_reportable_flights(result_df, flight_starts_with)
        # Reset index after filtering to maintain sequential indices
        result_df = result_df.reset_index(drop=True)


    # 1. CHECK FOR MISSING COLUMNS
    # Check if all required columns exist in the dataframe
    missing_columns = [col for col in all_required_columns if col not in result_df.columns]

    # If any columns are missing, mark errors and return False
    if missing_columns:
        print(f"Error: The following required columns are missing: {missing_columns}")

        # Log each missing column as a separate error
        for column in missing_columns:
            mark_error(
                column,
                f"Required column '{column}' is missing from the file",
                None,  # No specific row index since it affects the entire file
                "Column Missing",
                column
            )

        # Return False to indicate the file is incomplete, and empty string for file path
        output_file_json = generate_error_report(result_df, folder_path)
        return False, "",result_df, output_file_json
    
    # Sort the dataframe by Date, A/C Registration, and ATD
    result_df['Date'] = pd.to_datetime(result_df['Date'], dayfirst=True, errors='coerce')
    result_df.sort_values(by=['A/C Registration', 'Date', 'ATD (UTC) Block Off'], inplace=True)
    
    # Reset index after sorting but keep original indices for error tracking
    result_df = result_df.reset_index(drop=False)
    # Now 'index' column contains original row numbers, and the new index is 0,1,2...
    
    # 2. CENTRALIZED CHECK FOR MISSING VALUES IN ALL CELLS
    # This is a centralized check for all required columns
    print("Checking for missing cell values...")
    for idx, row in result_df.iterrows():
        # Use original row index for error tracking
        original_idx = row['index']

        for column in all_required_columns:
            value = row[column]
            value_str = str(value).strip() if not pd.isna(value) else ""

            # Check for missing data
            if pd.isna(value) or value_str == "":
                mark_error("Missing data", f"{column} is missing", original_idx, "Missing", column)
    
    # 3. CHECK FUEL TYPE VALUES - REMOVED
    # COMMENTED OUT: Fuel Type column has been removed from requirements
    # # Define allowed fuel types
    # allowed_fuel_types = ["Jet-A1", "Jet-A", "TS-1", "No. 3 Jet", "Jet-B", "AvGas"]
    #
    # print("Validating fuel types...")
    # for idx, row in result_df.iterrows():
    #     # Use original row index for error tracking
    #     original_idx = row['index']
    #
    #     if 'Fuel Type' in result_df.columns:
    #         fuel_type = row['Fuel Type']
    #         if not pd.isna(fuel_type) and str(fuel_type).strip() != "":
    #             if str(fuel_type) not in allowed_fuel_types:
    #                 mark_error(
    #                     str(fuel_type),
    #                     f"Invalid fuel type. Must be one of: {', '.join(allowed_fuel_types)}",
    #                     original_idx,
    #                     "Fuel",
    #                     "Fuel Type"
    #                 )
    
    # 4. FUEL CHECKING (Method-specific validation)
    print(f"Validating fuel data using method: {fuel_method}...")

    # Check each required fuel column for valid numeric values
    for idx, row in result_df.iterrows():
        # Use original row index for error tracking
        original_idx = row['index']

        for column in required_fuel_columns:
            if column in result_df.columns:
                # Get the value
                value = row[column]

                # We already checked for missing values in the centralized check
                # Now check if value is numeric
                try:
                    if not pd.isna(value):  # Only try to convert if not NaN
                        numeric_value = float(value)

                        # Additional validation: fuel values should be positive
                        if numeric_value < 0:
                            mark_error(value, f"{column} cannot be negative", original_idx, "Fuel", column)
                except (ValueError, TypeError):
                    mark_error(value, f"{column} must be numeric", original_idx, "Fuel", column)

    # Also check Fuel Consumption column (common to all methods)
    if 'Fuel Consumption' in result_df.columns:
        for idx, row in result_df.iterrows():
            original_idx = row['index']
            value = row['Fuel Consumption']

            try:
                if not pd.isna(value):
                    numeric_value = float(value)
                    if numeric_value < 0:
                        mark_error(value, "Fuel Consumption cannot be negative", original_idx, "Fuel", 'Fuel Consumption')
            except (ValueError, TypeError):
                mark_error(value, "Fuel Consumption must be numeric", original_idx, "Fuel", 'Fuel Consumption')

    # Method-specific validations
    if fuel_method == 'Block Off - Block On':
        # Block Off - Block On method validations
        print("Performing Block Off - Block On method validations...")

        # Check if Block Off Fuel > Block On Fuel
        if all(col in result_df.columns for col in ['Block Off Fuel', 'Block On Fuel']):
            for idx, row in result_df.iterrows():
                original_idx = row['index']

                try:
                    if (not pd.isna(row["Block Off Fuel"]) and not pd.isna(row["Block On Fuel"])):
                        block_off = float(row["Block Off Fuel"])
                        block_on = float(row["Block On Fuel"])

                        # Block off fuel should be greater than block on fuel
                        if block_off <= block_on:
                            mark_error(f"Off: {block_off}, On: {block_on}",
                                    "Block Off fuel must be greater than Block On fuel",
                                    original_idx, "Fuel", ["Block Off Fuel", "Block On Fuel"])
                except (ValueError, TypeError):
                    pass

        # Check fuel consumption consistency: Fuel Consumption = Block Off - Block On
        if all(col in result_df.columns for col in ['Block Off Fuel', 'Block On Fuel', 'Fuel Consumption']):
            for idx, row in result_df.iterrows():
                original_idx = row['index']

                try:
                    if (not pd.isna(row['Block Off Fuel']) and not pd.isna(row['Block On Fuel']) and
                        not pd.isna(row['Fuel Consumption'])):
                        block_off = float(row['Block Off Fuel'])
                        block_on = float(row['Block On Fuel'])
                        fuel_consumption = float(row['Fuel Consumption'])

                        # Calculate expected fuel consumption
                        expected_consumption = block_off - block_on

                        # Allow for a small tolerance (0.5% difference) due to rounding
                        tolerance = 0.005 * abs(expected_consumption) if expected_consumption != 0 else 0.01

                        if abs(expected_consumption - fuel_consumption) > tolerance:
                            mark_error(
                                f"Block Off: {block_off}, Block On: {block_on}, Consumption: {fuel_consumption}",
                                f"Fuel Consumption ({fuel_consumption}) doesn't match Block Off - Block On ({expected_consumption:.2f})",
                                original_idx, "Fuel", ['Block Off Fuel', 'Block On Fuel', 'Fuel Consumption']
                            )
                except (ValueError, TypeError):
                    pass

    elif fuel_method == 'Method B':
        # Method B validations
        print("Performing Method B validations...")

        # Check fuel consumption consistency: Fuel Consumption = (Remaining + Uplift) - Block On
        if all(col in result_df.columns for col in ['Remaining Fuel From Prev. Flight', 'Uplift weight', 'Block On Fuel', 'Fuel Consumption']):
            for idx, row in result_df.iterrows():
                original_idx = row['index']

                try:
                    if (not pd.isna(row['Remaining Fuel From Prev. Flight']) and
                        not pd.isna(row['Uplift weight']) and
                        not pd.isna(row['Block On Fuel']) and
                        not pd.isna(row['Fuel Consumption'])):

                        prev_fuel = float(row['Remaining Fuel From Prev. Flight'])
                        uplift = float(row['Uplift weight'])
                        block_on = float(row['Block On Fuel'])
                        fuel_consumption = float(row['Fuel Consumption'])

                        # Calculate expected fuel consumption using Method B
                        expected_consumption = (prev_fuel + uplift) - block_on

                        # Allow for a small tolerance (0.5% difference) due to rounding
                        tolerance = 0.005 * abs(expected_consumption) if expected_consumption != 0 else 0.01

                        if abs(expected_consumption - fuel_consumption) > tolerance:
                            mark_error(
                                f"Prev: {prev_fuel}, Uplift: {uplift}, Block On: {block_on}, Consumption: {fuel_consumption}",
                                f"Fuel Consumption ({fuel_consumption}) doesn't match (Prev + Uplift) - Block On ({expected_consumption:.2f})",
                                original_idx, "Fuel", ['Remaining Fuel From Prev. Flight', 'Uplift weight', 'Block On Fuel', 'Fuel Consumption']
                            )
                except (ValueError, TypeError):
                    pass
    
    # 5. DATE VALIDATION
    print("Validating dates...")
    if 'Date' in result_df.columns:
        for idx, row in result_df.iterrows():
            # Use original row index for error tracking
            original_idx = row['index']
            
            if not pd.isna(row['Date']):
                original_date = row['Date']
                date_str = str(original_date)
                date_obj = None
                
                # First, check if we have a datetime object or a string with timestamp
                try:
                    # Handle pandas Timestamp objects
                    if isinstance(original_date, pd.Timestamp):
                        date_obj = original_date.to_pydatetime()
                        # Update the dataframe with just the date portion in the preferred format
                        if date_format == "DMY":
                            result_df.at[idx, 'Date'] = date_obj.strftime("%d-%m-%Y")
                        else:  # MDY format
                            result_df.at[idx, 'Date'] = date_obj.strftime("%m-%d-%Y")
                        continue
                    
                    # Handle ISO format with timestamp (YYYY-MM-DD HH:MM:SS)
                    if ' ' in date_str and len(date_str) > 10:
                        # Extract just the date part (first 10 characters for YYYY-MM-DD)
                        if date_str[4] == '-' and date_str[7] == '-':  # Check if it's YYYY-MM-DD format
                            iso_date_part = date_str.split(' ')[0]
                            date_obj = datetime.strptime(iso_date_part, "%Y-%m-%d")
                            
                            # Update the dataframe with just the date portion in the preferred format
                            if date_format == "DMY":
                                result_df.at[idx, 'Date'] = date_obj.strftime("%d-%m-%Y")
                            else:  # MDY format
                                result_df.at[idx, 'Date'] = date_obj.strftime("%m-%d-%Y")
                            continue
                    
                    # For standard date formats from the original code
                    if date_format == "DMY":
                        # Try DD-MM-YYYY format
                        try:
                            date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                        except ValueError:
                            # Try DD/MM/YYYY format
                            try:
                                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                            except ValueError:
                                # Try YYYY-MM-DD format (ISO)
                                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                                # Convert to preferred format in the dataframe
                                result_df.at[idx, 'Date'] = date_obj.strftime("%d-%m-%Y")
                    else:  # MDY format
                        # Try MM-DD-YYYY format
                        try:
                            date_obj = datetime.strptime(date_str, "%m-%d-%Y")
                        except ValueError:
                            # Try MM/DD/YYYY format
                            try:
                                date_obj = datetime.strptime(date_str, "%m/%d/%Y")
                            except ValueError:
                                # Try YYYY-MM-DD format (ISO)
                                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                                # Convert to preferred format in the dataframe
                                result_df.at[idx, 'Date'] = date_obj.strftime("%m-%d-%Y")
                    
                    # Check if date is within specified range
                    if start_date and end_date and not (start_date <= date_obj <= end_date):
                        mark_error(date_str, f"Date not within range {start_date.date()} to {end_date.date()}", original_idx, "Date", "Date")
                        
                except (ValueError, TypeError) as e:
                    # Invalid date format
                    mark_error(date_str, f"Invalid date format: {e}", original_idx, "Date", "Date")
    
    
    # 7. ICAO CODE VALIDATION
    print("Validating ICAO codes...")
    required_icao_columns = ['Origin ICAO', 'Destination ICAO']
    
    # Check if reference CSV has the required columns
    if 'ICAO_Code' not in ref_df.columns or 'ICAO Member State' not in ref_df.columns:
        print("Warning: Reference CSV is missing required 'ICAO_Code' or 'ICAO Member State' columns.")
        print("Available columns:", ref_df.columns.tolist())
        # Create an empty dictionary as fallback
        icao_country_dict = {}
    else:
        # Create a dictionary for faster lookup
        icao_country_dict = dict(zip(ref_df['ICAO_Code'], ref_df['ICAO Member State']))
    
    # Validate ICAO codes
    for idx, row in result_df.iterrows():
        # Use original row index for error tracking
        original_idx = row['index']
        
        # Check Origin ICAO
        if 'Origin ICAO' in result_df.columns:
            origin_icao = row['Origin ICAO']
            if not pd.isna(origin_icao):
                # Validate the ICAO code
                is_valid, expected_country = validate_and_correct_icao(origin_icao,icao_country_dict)
                
                if not is_valid:
                    mark_error(str(origin_icao), "Invalid Origin ICAO", original_idx, "ICAO", "Origin ICAO")
                elif origin_icao not in icao_country_dict:
                    # Add the newly discovered valid ICAO code to the dictionary
                    icao_country_dict[origin_icao] = expected_country
        
        # Check Destination ICAO
        if 'Destination ICAO' in result_df.columns:
            dest_icao = row['Destination ICAO']
            if not pd.isna(dest_icao):
                # Validate the ICAO code
                is_valid, expected_country = validate_and_correct_icao(dest_icao,icao_country_dict)
                
                if not is_valid:
                    mark_error(str(dest_icao), "Invalid Destination ICAO", original_idx, "ICAO", "Destination ICAO")
                elif dest_icao not in icao_country_dict:
                    # Add the newly discovered valid ICAO code to the dictionary
                    icao_country_dict[dest_icao] = expected_country
    
    # 8. TIME FORMAT VALIDATION
    print("Validating time formats...")
    time_columns = ['ATD (UTC) Block Off', 'ATA (UTC) Block On']
    
    # Function to validate and convert time format
    def validate_and_convert_time(time_str):
        if pd.isna(time_str) or time_str == '':
            return None, False, "Missing time data"
        
        # Try different time formats and convert to HH:MM
        try:
            # If already in HH:MM format
            if isinstance(time_str, str) and re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', time_str):
                return time_str, True, None
            
            # If it's a datetime object
            if isinstance(time_str, (datetime, datetime.time)):
                formatted_time = time_str.strftime('%H:%M')
                return formatted_time, True, None
            
            # Try parsing various string formats
            if isinstance(time_str, str):
                # Try 12-hour format (e.g., "2:30 PM")
                try:
                    parsed_time = datetime.strptime(time_str, '%I:%M %p')
                    return parsed_time.strftime('%H:%M'), True, None
                except ValueError:
                    pass
                
                # Try other common formats
                formats = [
                    '%H.%M',        # 14.30
                    '%H,%M',        # 14,30
                    '%H %M',        # 14 30
                    '%H-%M',        # 14-30
                    '%I:%M%p',      # 2:30PM (no space)
                    '%I:%M %p',     # 2:30 PM
                    '%I.%M%p',      # 2.30PM
                    '%I.%M %p',     # 2.30 PM
                    '%I%M%p',       # 230PM
                    '%I %M %p',     # 2 30 PM
                    '%H%M',         # 1430 (military time)
                ]
                
                for fmt in formats:
                    try:
                        parsed_time = datetime.strptime(time_str, fmt)
                        return parsed_time.strftime('%H:%M'), True, None
                    except ValueError:
                        continue
                
                # If it's just a number (assume military time without colon)
                if time_str.isdigit() and len(time_str) == 4:
                    hours = int(time_str[:2])
                    minutes = int(time_str[2:])
                    if 0 <= hours <= 23 and 0 <= minutes <= 59:
                        return f"{hours:02d}:{minutes:02d}", True, None
            
            return time_str, False, "Cannot convert to HH:MM format"
        
        except Exception as e:
            return time_str, False, f"Error during time conversion: {str(e)}"
    
    # Validate time columns
    for idx, row in result_df.iterrows():
        # Use original row index for error tracking
        original_idx = row['index']
        
        for col in time_columns:
            if col in result_df.columns:
                time_value = row[col]
                if not pd.isna(time_value):
                    converted_time, is_valid, error_msg = validate_and_convert_time(time_value)
                    
                    if not is_valid:
                        mark_error(str(time_value), f"{col}: {error_msg}", original_idx, "Time", col)
                    elif converted_time != time_value:
                        # Update the time value in the dataframe if it was converted
                        result_df.at[idx, col] = converted_time
    
    
    
    
    
    
    
    
    
    
    
    
    # PRINT ERROR SUMMARY
    total_errors = sum(len(errors) for errors in error_tracker.values())
    print(f"\n📊 VALIDATION SUMMARY:")
    print(f"Found {total_errors} errors affecting {len(error_rows)} rows.")
    
    # Print summary by category
    if total_errors > 0:
        print("\nErrors by category:")
        for category in error_categories:
            if error_tracker[category]:
                print(f"  {category}: {len(error_tracker[category])} errors")
    else:
        print("✅ No validation errors found - all data appears to be valid according to current rules.")
        print("\nValidation rules checked:")
        print("  ✓ Missing column check")
        print("  ✓ Missing cell data check") 
        print("  ✓ Fuel type validation")
        print("  ✓ Fuel numeric validation")
        print("  ✓ Fuel calculation consistency")
        print("  ✓ Date format validation")
        print("  ✓ ICAO code validation")
        print("  ✓ Time format validation")
        print("  ✓ Flight sequence validation")
    
    # Check if there are "Column Missing" errors - critical issue
    if error_tracker["Column Missing"]:
        print("\nCritical error: Missing required columns - file cannot be processed")
        output_file_json = generate_error_report(result_df, folder_path)
        return False, "",result_df, output_file_json
    
    
    # After all validations, determine if file is valid
    has_column_errors = len(error_tracker["Column Missing"]) > 0
    

    print("\n\n" + str(result_df.iloc[6]) + "\n\n")
    # Generate output path
    if has_column_errors:
        # File has critical errors - don't save output
        output_file_json = generate_error_report(result_df, folder_path)
        return False, "",result_df,output_file_json
    else:
        # Save file with validation results
        base_name = os.path.splitext(file_path)[0]
        output_path = f"{base_name}_validated.csv"
        result_df.to_csv(output_path, index=False)
        print(f"File validated and saved to: {output_path}")
        
        # Return True if validation passed, but might have non-critical errors
        output_file_json = generate_error_report(result_df, folder_path)
        return True, output_path,result_df,output_file_json






def convert_to_serializable(value):
    """
    Convert pandas/numpy types to JSON serializable types
    """
    import numpy as np
    
    if pd.isna(value):
        return None
    elif hasattr(value, 'item'):  # numpy/pandas scalar
        return value.item()
    elif isinstance(value, (np.integer, np.int64, np.int32)):
        return int(value)
    elif isinstance(value, (np.floating, np.float64, np.float32)):
        return float(value)
    elif hasattr(value, 'strftime'):  # datetime objects
        return value.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return value


def flatten_columns(columns):
    """
    Flatten nested column lists and ensure all items are strings
    """
    flattened = []
    for item in columns:
        if isinstance(item, list):
            flattened.extend(flatten_columns(item))
        else:
            flattened.append(str(item))
    return flattened


def generate_error_report(result_df, output_path, auto_generate_csvs=True):
    """
    Generates a JSON report of all errors, grouped by category and reason.
    Stores row data in a central place to avoid duplication.
    Now includes structure optimization + LZ-String compression.
    Automatically generates clean_data.csv and errors_data.csv files.
    
    Parameters:
    - result_df: The DataFrame containing the data
    - output_path: Path to save the JSON file (optional)
    - auto_generate_csvs: Whether to automatically generate CSV files (default: True)
    
    Returns:
    - output_file_json: Path to the saved JSON file
    """
    global error_tracker, error_rows
    
    # Field mappings to reduce key repetition (for compression)
    field_map = {
        "Date": "d", "A/C Registration": "r", "Flight No": "f", "A/C Type": "t",
        "ATD (UTC) Block Off": "o", "ATA (UTC) Block On": "i",
        "Origin ICAO": "or", "Destination ICAO": "de", "Uplift Volume": "uv",
        "Uplift Density": "ud", "Uplift weight": "uw",
        "Remaining Fuel From Prev. Flight": "rf", "Block Off Fuel": "bf",
        "Block On Fuel": "bo", "Fuel Consumption": "fc"
    }
    
    # Reverse mapping for client-side decompression
    reverse_field_map = {v: k for k, v in field_map.items()}
    
    # Initialize the error report structure (original format)
    total_errors = sum(len(errors) for errors in error_tracker.values())
    error_report = {
        "summary": {
            "total_errors": total_errors,
            "error_rows": len(error_rows),
            "categories": {category: len(errors) for category, errors in error_tracker.items() if len(errors) > 0}
        },
        "rows_data": {},  # Central place to store row data
        "categories": []
    }
    
    # Create mapping from original indices to current pandas indices
    original_to_pandas_idx = {}
    for pandas_idx, row in result_df.iterrows():
        original_idx = row['index']
        original_to_pandas_idx[original_idx] = pandas_idx
    
    # Store all row data in a central place, indexed by row_idx
    for row_idx in error_rows:
        if row_idx is not None:  # Skip None indices (file-level errors)
            try:
                # Convert original index to current pandas index
                if row_idx in original_to_pandas_idx:
                    pandas_idx = original_to_pandas_idx[row_idx]
                    # Get row data using the correct pandas index
                    row_data = result_df.iloc[pandas_idx].to_dict()
                else:
                    print(f"Warning: Original row_idx {row_idx} not found in current DataFrame")
                    continue
                
                row_data = {k: convert_to_serializable(v) for k, v in row_data.items()}
                
                # Strip " 00:00:00" suffix from Date field
                if "Date" in row_data:
                    if hasattr(row_data["Date"], 'strftime'):  # Check if it's a datetime-like object
                        # Convert to date string (YYYY-MM-DD format)
                        row_data["Date"] = row_data["Date"].strftime("%Y-%m-%d")
                    elif isinstance(row_data["Date"], str) and row_data["Date"].endswith(" 00:00:00"):
                        # Handle string dates
                        row_data["Date"] = row_data["Date"].split(" ")[0]
                
                # Round all numeric values to 3 decimal places
                for key, value in row_data.items():
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        row_data[key] = round(float(value), 3)
                
                error_report["rows_data"][str(row_idx)] = row_data
            except (IndexError, AttributeError):
                error_report["rows_data"][str(row_idx)] = {"error": "Row not found in DataFrame"}
    
    # Process each category
    for category in sorted(error_tracker.keys()):
        if not error_tracker[category]:
            continue  # Skip empty categories
        
        # Group errors by reason within this category
        errors_by_reason = defaultdict(list)
        for error in error_tracker[category]:
            reason = error["reason"]
            errors_by_reason[reason].append(error)
        
        # Create category entry
        category_entry = {
            "name": category,
            "errors": []
        }
        
        # Process each reason group, sorted alphabetically
        for reason in sorted(errors_by_reason.keys()):
            reason_group = {
                "reason": reason,
                "rows": []
            }
            
            # Add each error row
            for error in errors_by_reason[reason]:
                row_idx = error["row_idx"]
                
                # Skip if row_idx is None (applies to the whole file, not a specific row)
                if row_idx is None:
                    # For file-level errors like missing columns
                    file_error = {
                        "file_level": True,
                        "cell_data": error["cell_data"],
                        "columns": error["columns"]
                    }
                    reason_group["rows"].append(file_error)
                    continue
                
                # Add error row entry with reference to central row data
                row_entry = {
                    "row_idx": row_idx,
                    "cell_data": error["cell_data"],
                    "columns": error["columns"]
                }
                
                reason_group["rows"].append(row_entry)
            
            # Add reason group to category
            category_entry["errors"].append(reason_group)
        
        # Add category to report
        error_report["categories"].append(category_entry)
    
    # Save original JSON format
    output_file = None
    if output_path:
        # Generate filename if only directory is provided
        if os.path.isdir(output_path):
            output_file = os.path.join(output_path, "error_report.json")
        else:
            output_file = output_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # Write original JSON to file
        json_str = json.dumps(error_report, indent=2, default=str, ensure_ascii=False)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_str)
    
    # Create compressed version for web transfer
    try:
        compressed_data = create_compressed_error_report(error_report, field_map, reverse_field_map)
        
        # Save compressed version
        if output_path:
            if os.path.isdir(output_path):
                compressed_file = os.path.join(output_path, "error_report.lzs")
            else:
                compressed_file = output_path.replace('.json', '.lzs')
            
            with open(compressed_file, 'w', encoding='utf-8') as f:
                f.write(compressed_data)
            
            print(f"Compressed file saved to: {compressed_file}")
    
    except Exception as e:
        print(f"Warning: Failed to create compressed version: {e}")
        # Continue with original functionality
    
    # Auto-generate clean and errors CSV files (only if enabled and JSON file was created successfully)
    if auto_generate_csvs and output_file and os.path.exists(output_file):
        try:
            # Create a DataFrame with original indices for CSV processing
            # We need to restore the original index mapping for the CSV function to work correctly
            csv_df = result_df.copy()
            csv_df.index = csv_df['index']  # Set the index to original indices
            csv_df = csv_df.drop('index', axis=1)  # Remove the 'index' column
            
            clean_csv_path, errors_csv_path = process_error_json_to_csvs(
                json_file_path=output_file,
                original_data_df=csv_df,
                output_dir=output_path if output_path and os.path.isdir(output_path) else os.path.dirname(output_file)
            )
            
            if clean_csv_path and errors_csv_path:
                print(f"Auto-generated CSV files:")
                print(f"  Clean data: {clean_csv_path}")
                print(f"  Error data: {errors_csv_path}")
            else:
                print("Warning: Failed to auto-generate CSV files")
                
        except Exception as e:
            print(f"Warning: Failed to auto-generate CSV files: {e}")
            import traceback
            traceback.print_exc()
    
    # Reset error tracking for next use
    error_tracker = {category: [] for category in error_categories}
    error_rows = set()
    
    return output_file


def create_compressed_error_report(error_data, field_map, reverse_field_map):
    """
    Create compressed version of error report using structure optimization + LZ-String
    """
    try:
        # Optimize row data structure
        optimized_rows = {}
        for row_idx, row_data in error_data.get('rows_data', {}).items():
            optimized_row = {}
            
            for key, value in row_data.items():
                if key == 'error':
                    optimized_row['err'] = value
                else:
                    short_key = field_map.get(key, key)
                    
                    # Convert and optimize numeric values
                    value = convert_to_serializable(value)
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        rounded_value = round(float(value), 3)
                        if rounded_value == int(rounded_value):
                            value = int(rounded_value)
                        else:
                            value = rounded_value
                    
                    optimized_row[short_key] = value
            
            optimized_rows[row_idx] = optimized_row
        
        # Optimize error structure
        optimized_categories = []
        for category in error_data.get('categories', []):
            category_errors = []
            
            for error_group in category.get('errors', []):
                reason_data = {
                    "r": error_group.get('reason', ''),  # reason
                    "rows": []
                }
                
                for row_error in error_group.get('rows', []):
                    if row_error.get('file_level'):
                        row_entry = {
                            "fl": True,  # file_level
                            "cd": row_error.get('cell_data', ''),  # cell_data
                            "cols": row_error.get('columns', [])
                        }
                    else:
                        row_entry = {
                            "idx": row_error.get('row_idx'),  # row_idx
                            "cd": row_error.get('cell_data', ''),  # cell_data
                            "cols": row_error.get('columns', [])
                        }
                    
                    reason_data["rows"].append(row_entry)
                
                category_errors.append(reason_data)
            
            optimized_categories.append({
                "n": category.get('name', ''),  # name
                "e": category_errors  # errors
            })
        
        # Create optimized report
        summary = error_data.get('summary', {})
        optimized_report = {
            "meta": {
                "fm": reverse_field_map,  # field map for decompression
                "s": {  # summary
                    "te": convert_to_serializable(summary.get('total_errors', 0)),  # total_errors
                    "er": convert_to_serializable(summary.get('error_rows', 0)),  # error_rows
                    "c": {k: convert_to_serializable(v) for k, v in summary.get('categories', {}).items()}  # categories
                }
            },
            "rd": optimized_rows,  # rows_data
            "c": optimized_categories  # categories
        }
        
        # Convert to compact JSON
        json_str = json.dumps(optimized_report, separators=(',', ':'), ensure_ascii=False)
        
        # Compress with LZ-String
        compressed_data = LZString.compressToBase64(json_str)
        
        # Calculate compression stats
        original_size = len(json_str.encode('utf-8'))
        compressed_size = len(compressed_data.encode('utf-8'))
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        print(f"JSON Optimization + LZ-String Compression:")
        print(f"  Original size: {original_size:,} bytes")
        print(f"  Compressed size: {compressed_size:,} bytes")
        print(f"  Compression ratio: {compression_ratio:.1f}%")
        
        return compressed_data
        
    except Exception as e:
        print(f"Error compressing data: {e}")
        # Fallback: return uncompressed JSON
        json_str = json.dumps(error_data, separators=(',', ':'), ensure_ascii=False)
        return json_str


def process_error_json_to_csvs(json_file_path, original_data_df, output_dir=None):
    """
    Process a JSON error report to create two CSV files:
    1. Clean CSV: Contains all rows except those with errors
    2. Errors CSV: Contains only error rows, organized by category and error type
    
    Parameters:
    - json_file_path: Path to the JSON error report file
    - original_data_df: The original DataFrame containing all data
    - output_dir: Directory to save the CSV files (defaults to same directory as JSON file)
    
    Returns:
    - tuple: (clean_csv_path, errors_csv_path) or (None, None) if processing fails
    """
    
    try:
        # Load the JSON error report
        with open(json_file_path, 'r', encoding='utf-8') as f:
            error_data = json.load(f)
        
        # Extract all error row indices
        error_row_indices = set()
        
        # Get error rows from categories
        for category in error_data.get('categories', []):
            for error_group in category.get('errors', []):
                for row_error in error_group.get('rows', []):
                    if not row_error.get('file_level', False):  # Skip file-level errors
                        row_idx = row_error.get('row_idx')
                        if row_idx is not None:
                            # Convert string indices to integers for consistency
                            try:
                                row_idx = int(row_idx)
                                error_row_indices.add(row_idx)
                            except (ValueError, TypeError):
                                print(f"Warning: Invalid row_idx '{row_idx}' - skipping")
                                continue
        
        # Determine output directory
        if output_dir is None:
            output_dir = os.path.dirname(json_file_path)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. CREATE CLEAN CSV (all rows except error rows)
        clean_df = original_data_df.loc[~original_data_df.index.isin(error_row_indices)].copy()
        clean_csv_path = os.path.join(output_dir, 'clean_data.csv')
        clean_df.to_csv(clean_csv_path, index=False)
        
        print(f"🧹 Clean CSV created with {len(clean_df)} rows (out of {len(original_data_df)} total): {clean_csv_path}")
        
        # 2. CREATE ERRORS CSV (only error rows, organized by category and error type)
        errors_data = []
        
        # Process each category
        for category in error_data.get('categories', []):
            category_name = category.get('name', 'Unknown')
            
            for error_group in category.get('errors', []):
                error_reason = error_group.get('reason', 'Unknown Error')
                
                for row_error in error_group.get('rows', []):
                    if row_error.get('file_level', False):
                        # Handle file-level errors
                        error_row = {
                            'Error_Category': category_name,
                            'Error_Reason': error_reason,
                            'Row_Index': 'File-level',
                            'Affected_Columns': ', '.join(flatten_columns(row_error.get('columns', []))),
                            'Cell_Data': str(row_error.get('cell_data', ''))
                        }
                        # Add all original columns with empty values for file-level errors
                        for col in original_data_df.columns:
                            error_row[col] = ''
                        
                        errors_data.append(error_row)
                    else:
                        # Handle row-level errors
                        row_idx = row_error.get('row_idx')
                        if row_idx is not None:
                            # Convert string indices to integers for consistency
                            try:
                                row_idx = int(row_idx)
                            except (ValueError, TypeError):
                                print(f"Warning: Invalid row_idx '{row_idx}' in error processing - skipping")
                                continue
                            
                            if row_idx in original_data_df.index:
                                # Get the original row data
                                original_row = original_data_df.loc[row_idx].to_dict()
                                
                                # Clean up the row data (handle datetime objects, etc.)
                                for key, value in original_row.items():
                                    original_row[key] = convert_to_serializable(value)
                                    if hasattr(value, 'strftime'):  # datetime object
                                        if key == "Date":
                                            original_row[key] = value.strftime("%Y-%m-%d")
                                        else:
                                            original_row[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                                    elif pd.isna(value):
                                        original_row[key] = ''
                                    elif isinstance(original_row[key], (int, float)) and not isinstance(original_row[key], bool):
                                        original_row[key] = round(float(original_row[key]), 3)
                                
                                # Create error row with metadata
                                error_row = {
                                    'Error_Category': category_name,
                                    'Error_Reason': error_reason,
                                    'Row_Index': row_idx,
                                    'Affected_Columns': ', '.join(flatten_columns(row_error.get('columns', []))),
                                    'Cell_Data': str(row_error.get('cell_data', ''))
                                }
                                
                                # Add all original data columns
                                error_row.update(original_row)
                                
                                errors_data.append(error_row)
                            else:
                                print(f"Warning: Row index {row_idx} not found in original data - skipping")
        
        # Create errors DataFrame and save to CSV
        if errors_data:
            errors_df = pd.DataFrame(errors_data)
            
            # Reorder columns to put error metadata first
            error_metadata_cols = ['Error_Category', 'Error_Reason', 'Row_Index', 'Affected_Columns', 'Cell_Data']
            original_cols = [col for col in original_data_df.columns if col not in error_metadata_cols]
            column_order = error_metadata_cols + original_cols
            
            # Ensure all columns exist (some might be missing for file-level errors)
            for col in column_order:
                if col not in errors_df.columns:
                    errors_df[col] = ''
            
            errors_df = errors_df[column_order]
            
            errors_csv_path = os.path.join(output_dir, 'errors_data.csv')
            errors_df.to_csv(errors_csv_path, index=False)
            
            print(f"⚠️  Errors CSV created with {len(errors_df)} error entries: {errors_csv_path}")
            
            # Show breakdown by category
            category_counts = errors_df['Error_Category'].value_counts()
            print(f"   Error breakdown: {dict(category_counts)}")
        else:
            # Create empty errors CSV if no errors found
            errors_df = pd.DataFrame(columns=['Error_Category', 'Error_Reason', 'Row_Index', 'Affected_Columns', 'Cell_Data'] + list(original_data_df.columns))
            errors_csv_path = os.path.join(output_dir, 'errors_data.csv')
            errors_df.to_csv(errors_csv_path, index=False)
            
            print(f"✅ Empty errors CSV created (no validation errors detected): {errors_csv_path}")
            print(f"   This means all {len(original_data_df)} rows passed validation checks.")
        
        return clean_csv_path, errors_csv_path
        
    except Exception as e:
        print(f"Error processing JSON to CSV: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


def generate_csvs_from_json_report(json_file_path, original_csv_path=None, original_df=None, output_dir=None):
    """
    Convenience function to generate clean and errors CSV files from a JSON error report.
    
    Parameters:
    - json_file_path: Path to the JSON error report file
    - original_csv_path: Path to the original CSV file (optional if original_df is provided)
    - original_df: Original DataFrame (optional if original_csv_path is provided)
    - output_dir: Directory to save the CSV files (defaults to same directory as JSON file)
    
    Returns:
    - tuple: (clean_csv_path, errors_csv_path) or (None, None) if processing fails
    """
    
    # Load original data if not provided
    if original_df is None:
        if original_csv_path is None:
            print("Error: Either original_csv_path or original_df must be provided")
            return None, None
        
        try:
            # Detect encoding and load CSV
            encoding = 'utf-8'
            try:
                import chardet
                with open(original_csv_path, 'rb') as f:
                    raw_data = f.read()
                    result = chardet.detect(raw_data)
                    encoding = result['encoding'] or 'utf-8'
            except ImportError:
                pass
            
            original_df = pd.read_csv(original_csv_path, encoding=encoding, encoding_errors='replace')
        except Exception as e:
            print(f"Error loading original CSV file: {str(e)}")
            return None, None
    
    return process_error_json_to_csvs(json_file_path, original_df, output_dir)


def detect_encoding(file_path):
    """Detect file encoding with better handling"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            
        encoding = result['encoding']
        confidence = result['confidence']
        
        # If confidence is low, fallback to common encodings
        if confidence < 0.7:
            for fallback_encoding in ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=fallback_encoding) as f:
                        f.read()
                    return fallback_encoding
                except UnicodeDecodeError:
                    continue
        
        return encoding if encoding else 'utf-8'
    except Exception:
        return 'utf-8'


def safe_json_load(file_path):
    """Safely load JSON file with proper encoding detection"""
    if not os.path.exists(file_path):
        return None
    
    # For JSON files, try common encodings
    encodings_to_try = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
    
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    
    # If all fail, try detecting encoding
    detected_encoding = detect_encoding(file_path)
    try:
        with open(file_path, 'r', encoding=detected_encoding) as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load JSON file {file_path}: {e}")
        return None