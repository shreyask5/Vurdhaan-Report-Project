import pandas as pd
from helpers.config import get_eea_states, get_uk_state, get_switzerland_state, LIECHTENSTEIN_ICAO


def filter_reportable_flights(df, flight_starts_with, icao_error_rows=None):
    """
    Filter flights for EU ETS reporting based on route criteria and flight prefix.

    This function filters flights to include only those that are reportable under EU ETS:
    - EEA to EEA flights (with different ICAO codes for same country)
    - EEA to United Kingdom flights
    - EEA to Switzerland flights

    Parameters:
    - df (DataFrame): Input dataframe containing flight data (with 'index' column from reset_index)
    - flight_starts_with (str): Flight prefix filter (e.g., "ABC" for flights starting with "ABC")
    - icao_error_rows (set): Set of row indices with ICAO errors that should be preserved

    Returns:
    - DataFrame: Filtered dataframe containing only EU ETS reportable flights (preserves 'index' column)
    """
    print("Filtering EU ETS reportable flights...")

    # Make a copy to avoid modifying the original
    filtered_df = df.copy()

    # Add Departure Country and Arriving Country using airports.csv
    try:
        # Load the airports.csv file
        airports_df = pd.read_csv('airports.csv', encoding='utf-8')
        
        # Create a mapping dictionary from ICAO_Code to ICAO Member State
        icao_to_country = dict(zip(airports_df['ICAO_Code'], airports_df['ICAO Member State']))
        
        # Map Origin ICAO to Departure Country
        if 'Origin ICAO' in filtered_df.columns:
            filtered_df['Departure Country'] = filtered_df['Origin ICAO'].map(icao_to_country)
            print("Added 'Departure Country' column based on Origin ICAO mapping")
        else:
            print("Warning: 'Origin ICAO' column not found in processed data")
        
        # Map Destination ICAO to Arriving Country
        if 'Destination ICAO' in filtered_df.columns:
            filtered_df['Arriving Country'] = filtered_df['Destination ICAO'].map(icao_to_country)
            print("Added 'Arriving Country' column based on Destination ICAO mapping")
        else:
            print("Warning: 'Destination ICAO' column not found in processed data")
            
    except FileNotFoundError:
        print("Warning: airports.csv file not found. Cannot add country information.")
    except KeyError as e:
        print(f"Warning: Required column missing in airports.csv: {e}")
    except Exception as e:
        print(f"Warning: Error processing airports data: {str(e)}")

    # Get EEA states and special countries
    eea_states = set(get_eea_states())
    uk_state = get_uk_state()
    switzerland_state = get_switzerland_state()

    # Track rows to delete
    rows_to_delete = []

    # Flight validation - check both 'Flight No' and 'Flight' column names
    flight_column = None
    if 'Flight No' in filtered_df.columns:
        flight_column = 'Flight No'
    elif 'Flight' in filtered_df.columns:
        flight_column = 'Flight'

    if flight_column and flight_starts_with:
        print(f"Validating flight numbers against prefix: {flight_starts_with}")
        for idx, row in filtered_df.iterrows():
            if not pd.isna(row[flight_column]):
                flight_str = str(row[flight_column])
                if not flight_str.startswith(flight_starts_with):
                    # Mark for deletion
                    if idx not in rows_to_delete:
                        rows_to_delete.append(idx)

    # EU ETS route filtering
    if 'Departure Country' in filtered_df.columns and 'Arriving Country' in filtered_df.columns:
        print("Applying EU ETS route filtering...")
        for idx, row in filtered_df.iterrows():
            original_idx = row['index'] if 'index' in row else idx
            
            # Skip if this row has ICAO errors
            if icao_error_rows and original_idx in icao_error_rows:
                continue
                
            # Check if both countries exist
            if pd.isna(row['Departure Country']) or pd.isna(row['Arriving Country']):
                if idx not in rows_to_delete:
                    rows_to_delete.append(idx)
                continue
            
            departure_country = row['Departure Country']
            arriving_country = row['Arriving Country']
            
            # Check if departure is from EEA (including Liechtenstein special case)
            is_departure_eea = (departure_country in eea_states or 
                              (row.get('Origin ICAO') == LIECHTENSTEIN_ICAO))
            
            # Check if arrival is to EEA, UK, or Switzerland (including Liechtenstein special case)
            is_arrival_eea = arriving_country in eea_states
            is_arrival_uk = arriving_country == uk_state
            is_arrival_switzerland = arriving_country == switzerland_state
            is_arrival_liechtenstein = row.get('Destination ICAO') == LIECHTENSTEIN_ICAO
            
            is_arrival_valid = (is_arrival_eea or is_arrival_uk or 
                              is_arrival_switzerland or is_arrival_liechtenstein)
            
            # Keep flights if: departure from EEA AND arrival to EEA/UK/Switzerland
            if not (is_departure_eea and is_arrival_valid):
                if idx not in rows_to_delete:
                    rows_to_delete.append(idx)
                continue
            
            # For EEA to EEA same country flights, ensure different ICAO codes
            if (is_departure_eea and is_arrival_eea and 
                departure_country == arriving_country and
                not is_arrival_liechtenstein):  # Liechtenstein exception handled above
                
                origin_icao = row.get('Origin ICAO')
                destination_icao = row.get('Destination ICAO')
                
                # Remove if same ICAO codes (same airport)
                if (origin_icao and destination_icao and 
                    origin_icao == destination_icao):
                    if idx not in rows_to_delete:
                        rows_to_delete.append(idx)

    # Remove rows that don't match criteria
    if rows_to_delete:
        print(f"Removing {len(rows_to_delete)} rows that don't match EU ETS criteria")
        filtered_df = filtered_df.drop(rows_to_delete)
        # DON'T reset index here - preserve the 'index' column for error tracking
    else:
        print("All flights match the EU ETS criteria")

    print(f"EU ETS reportable flights: {len(filtered_df)} rows")
    return filtered_df
