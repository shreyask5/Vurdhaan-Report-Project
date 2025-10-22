"""
Regulatory Configuration Data for Aviation Reporting Schemes

This module contains regulatory information for various aviation reporting schemes,
including CORSIA (Carbon Offsetting and Reduction Scheme for International Aviation).

The data is organized by scheme and year to support historical and current reporting.
"""

# Special ICAO codes for EU ETS
LIECHTENSTEIN_ICAO = "LSXB"

# CORSIA States by Year
# Source: ICAO CORSIA participation lists
REGULATORY_DATA = {
    'EU_ETS': {
        'EEA_STATES': [
            "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czechia", "Denmark", "Estonia",
            "Finland", "France", "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Italy",
            "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands", "Norway", "Poland",
            "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden"
        ],
        'UK': "United Kingdom",
        'SWITZERLAND': "Switzerland"
    },
    'CORSIA': {
        2020: {
            'states': [
                "Afghanistan", "Albania", "Antigua and Barbuda", "Armenia", "Australia", "Austria", "Azerbaijan",
                "Bahamas", "Bahrain", "Barbados", "Belgium", "Belize", "Benin", "Bosnia and Herzegovina",
                "Botswana", "Bulgaria", "Burkina Faso", "Cambodia", "Cameroon", "Canada", "Cook Islands",
                "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia",
                "Democratic Republic of the Congo", "Denmark", "Dominican Republic", "Ecuador",
                "El Salvador", "Equatorial Guinea", "Estonia", "Finland", "France", "Gabon", "Gambia",
                "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guyana", "Haiti",
                "Honduras", "Hungary", "Iceland", "Indonesia", "Iraq", "Ireland", "Israel", "Italy",
                "Jamaica", "Japan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Latvia", "Lithuania",
                "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta",
                "Marshall Islands", "Mauritius", "Mexico", "Micronesia (Federated States of)", "Monaco",
                "Montenegro", "Namibia", "Nauru", "Netherlands", "New Zealand", "Nigeria", "North Macedonia",
                "Norway", "Oman", "Palau", "Papua New Guinea", "Philippines", "Poland", "Portugal",
                "Qatar", "Republic of Korea", "Republic of Moldova", "Romania", "Rwanda", "Saint Kitts and Nevis",
                "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Saudi Arabia", "Serbia",
                "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
                "South Sudan", "Spain", "Suriname", "Sweden", "Switzerland", "Thailand", "Timor-Leste",
                "Tonga", "Trinidad and Tobago", "Türkiye", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates",
                "United Kingdom", "United Republic of Tanzania", "United States", "Uruguay", "Vanuatu",
                "Zambia", "Zimbabwe"
            ]
        },
        2021: {
            'states': [
                "Afghanistan", "Albania", "Antigua and Barbuda", "Armenia", "Australia", "Austria", "Azerbaijan",
                "Bahamas", "Bahrain", "Barbados", "Belgium", "Belize", "Benin", "Bosnia and Herzegovina",
                "Botswana", "Bulgaria", "Burkina Faso", "Cambodia", "Cameroon", "Canada", "Cook Islands",
                "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia",
                "Democratic Republic of the Congo", "Denmark", "Dominican Republic", "Ecuador",
                "El Salvador", "Equatorial Guinea", "Estonia", "Finland", "France", "Gabon", "Gambia",
                "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guyana", "Haiti",
                "Honduras", "Hungary", "Iceland", "Indonesia", "Iraq", "Ireland", "Israel", "Italy",
                "Jamaica", "Japan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Latvia", "Lithuania",
                "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta",
                "Marshall Islands", "Mauritius", "Mexico", "Micronesia (Federated States of)", "Monaco",
                "Montenegro", "Namibia", "Nauru", "Netherlands", "New Zealand", "Nigeria", "North Macedonia",
                "Norway", "Oman", "Palau", "Papua New Guinea", "Philippines", "Poland", "Portugal",
                "Qatar", "Republic of Korea", "Republic of Moldova", "Romania", "Rwanda", "Saint Kitts and Nevis",
                "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Saudi Arabia", "Serbia",
                "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
                "South Sudan", "Spain", "Suriname", "Sweden", "Switzerland", "Thailand", "Timor-Leste",
                "Tonga", "Trinidad and Tobago", "Türkiye", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates",
                "United Kingdom", "United Republic of Tanzania", "United States", "Uruguay", "Vanuatu",
                "Zambia", "Zimbabwe"
            ]
        },
        2022: {
            'states': [
                "Afghanistan", "Albania", "Antigua and Barbuda", "Armenia", "Australia", "Austria", "Azerbaijan",
                "Bahamas", "Bahrain", "Barbados", "Belgium", "Belize", "Benin", "Bosnia and Herzegovina",
                "Botswana", "Bulgaria", "Burkina Faso", "Cambodia", "Cameroon", "Canada", "Cook Islands",
                "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia",
                "Democratic Republic of the Congo", "Denmark", "Dominican Republic", "Ecuador",
                "El Salvador", "Equatorial Guinea", "Estonia", "Finland", "France", "Gabon", "Gambia",
                "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guyana", "Haiti",
                "Honduras", "Hungary", "Iceland", "Indonesia", "Iraq", "Ireland", "Israel", "Italy",
                "Jamaica", "Japan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Latvia", "Lithuania",
                "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta",
                "Marshall Islands", "Mauritius", "Mexico", "Micronesia (Federated States of)", "Monaco",
                "Montenegro", "Namibia", "Nauru", "Netherlands", "New Zealand", "Nigeria", "North Macedonia",
                "Norway", "Oman", "Palau", "Papua New Guinea", "Philippines", "Poland", "Portugal",
                "Qatar", "Republic of Korea", "Republic of Moldova", "Romania", "Rwanda", "Saint Kitts and Nevis",
                "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Saudi Arabia", "Serbia",
                "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
                "South Sudan", "Spain", "Suriname", "Sweden", "Switzerland", "Thailand", "Timor-Leste",
                "Tonga", "Trinidad and Tobago", "Türkiye", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates",
                "United Kingdom", "United Republic of Tanzania", "United States", "Uruguay", "Vanuatu",
                "Zambia", "Zimbabwe"
            ]
        },
        2023: {
            'states': [
                "Afghanistan", "Albania", "Antigua and Barbuda", "Armenia", "Australia", "Austria", "Azerbaijan",
                "Bahamas", "Bahrain", "Barbados", "Belgium", "Belize", "Benin", "Bosnia and Herzegovina",
                "Botswana", "Bulgaria", "Burkina Faso", "Cambodia", "Cameroon", "Canada", "Cook Islands",
                "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia",
                "Democratic Republic of the Congo", "Denmark", "Dominican Republic", "Ecuador",
                "El Salvador", "Equatorial Guinea", "Estonia", "Finland", "France", "Gabon", "Gambia",
                "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guyana", "Haiti",
                "Honduras", "Hungary", "Iceland", "Indonesia", "Iraq", "Ireland", "Israel", "Italy",
                "Jamaica", "Japan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Latvia", "Lithuania",
                "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta",
                "Marshall Islands", "Mauritius", "Mexico", "Micronesia (Federated States of)", "Monaco",
                "Montenegro", "Namibia", "Nauru", "Netherlands", "New Zealand", "Nigeria", "North Macedonia",
                "Norway", "Oman", "Palau", "Papua New Guinea", "Philippines", "Poland", "Portugal",
                "Qatar", "Republic of Korea", "Republic of Moldova", "Romania", "Rwanda", "Saint Kitts and Nevis",
                "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Saudi Arabia", "Serbia",
                "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
                "South Sudan", "Spain", "Suriname", "Sweden", "Switzerland", "Thailand", "Timor-Leste",
                "Tonga", "Trinidad and Tobago", "Türkiye", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates",
                "United Kingdom", "United Republic of Tanzania", "United States", "Uruguay", "Vanuatu",
                "Zambia", "Zimbabwe"
            ]
        },
        2024: {
            'states': [
                "Afghanistan", "Albania", "Antigua and Barbuda", "Armenia", "Australia", "Austria", "Azerbaijan",
                "Bahamas", "Bahrain", "Barbados", "Belgium", "Belize", "Benin", "Bosnia and Herzegovina",
                "Botswana", "Bulgaria", "Burkina Faso", "Cambodia", "Cameroon", "Canada", "Cook Islands",
                "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia",
                "Democratic Republic of the Congo", "Denmark", "Dominican Republic", "Ecuador",
                "El Salvador", "Equatorial Guinea", "Estonia", "Finland", "France", "Gabon", "Gambia",
                "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guyana", "Haiti",
                "Honduras", "Hungary", "Iceland", "Indonesia", "Iraq", "Ireland", "Israel", "Italy",
                "Jamaica", "Japan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Latvia", "Lithuania",
                "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta",
                "Marshall Islands", "Mauritius", "Mexico", "Micronesia (Federated States of)", "Monaco",
                "Montenegro", "Namibia", "Nauru", "Netherlands", "New Zealand", "Nigeria", "North Macedonia",
                "Norway", "Oman", "Palau", "Papua New Guinea", "Philippines", "Poland", "Portugal",
                "Qatar", "Republic of Korea", "Republic of Moldova", "Romania", "Rwanda", "Saint Kitts and Nevis",
                "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Saudi Arabia", "Serbia",
                "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
                "South Sudan", "Spain", "Suriname", "Sweden", "Switzerland", "Thailand", "Timor-Leste",
                "Tonga", "Trinidad and Tobago", "Türkiye", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates",
                "United Kingdom", "United Republic of Tanzania", "United States", "Uruguay", "Vanuatu",
                "Zambia", "Zimbabwe"
            ]
        },
        2025: {
            'states': [
                "Afghanistan", "Albania", "Antigua and Barbuda", "Armenia", "Australia", "Austria", "Azerbaijan",
                "Bahamas", "Bahrain", "Barbados", "Belgium", "Belize", "Benin", "Bosnia and Herzegovina",
                "Botswana", "Bulgaria", "Burkina Faso", "Cambodia", "Cameroon", "Canada", "Cook Islands",
                "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia",
                "Democratic Republic of the Congo", "Denmark", "Dominican Republic", "Ecuador",
                "El Salvador", "Equatorial Guinea", "Estonia", "Finland", "France", "Gabon", "Gambia",
                "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guyana", "Haiti",
                "Honduras", "Hungary", "Iceland", "Indonesia", "Iraq", "Ireland", "Israel", "Italy",
                "Jamaica", "Japan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Latvia", "Lithuania",
                "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta",
                "Marshall Islands", "Mauritius", "Mexico", "Micronesia (Federated States of)", "Monaco",
                "Montenegro", "Namibia", "Nauru", "Netherlands", "New Zealand", "Nigeria", "North Macedonia",
                "Norway", "Oman", "Palau", "Papua New Guinea", "Philippines", "Poland", "Portugal",
                "Qatar", "Republic of Korea", "Republic of Moldova", "Romania", "Rwanda", "Saint Kitts and Nevis",
                "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Saudi Arabia", "Serbia",
                "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
                "South Sudan", "Spain", "Suriname", "Sweden", "Switzerland", "Thailand", "Timor-Leste",
                "Tonga", "Trinidad and Tobago", "Türkiye", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates",
                "United Kingdom", "United Republic of Tanzania", "United States", "Uruguay", "Vanuatu",
                "Zambia", "Zimbabwe"
            ]
        }
    }
}


def get_corsia_states(year=2024):
    """
    Retrieve CORSIA participating states for a specific year.

    Parameters:
    - year (int): The year for which to retrieve CORSIA states (default: 2024)

    Returns:
    - list: List of CORSIA participating state names

    Raises:
    - ValueError: If the year is not available in the configuration
    """
    if year not in REGULATORY_DATA['CORSIA']:
        available_years = sorted(REGULATORY_DATA['CORSIA'].keys())
        raise ValueError(f"CORSIA data not available for year {year}. Available years: {available_years}")

    return REGULATORY_DATA['CORSIA'][year]['states']


def get_available_years(scheme='CORSIA'):
    """
    Get all available years for a specific reporting scheme.

    Parameters:
    - scheme (str): The reporting scheme name (default: 'CORSIA')

    Returns:
    - list: Sorted list of available years
    """
    if scheme not in REGULATORY_DATA:
        raise ValueError(f"Scheme '{scheme}' not found in regulatory data")

    return sorted(REGULATORY_DATA[scheme].keys())


def get_eea_states():
    """
    Retrieve EEA member states for EU ETS reporting.

    Returns:
    - list: List of EEA member state names
    """
    return REGULATORY_DATA['EU_ETS']['EEA_STATES']


def get_uk_state():
    """
    Retrieve UK state name for EU ETS reporting.

    Returns:
    - str: UK state name
    """
    return REGULATORY_DATA['EU_ETS']['UK']


def get_switzerland_state():
    """
    Retrieve Switzerland state name for EU ETS reporting.

    Returns:
    - str: Switzerland state name
    """
    return REGULATORY_DATA['EU_ETS']['SWITZERLAND']


def validate_scheme_year(scheme='CORSIA', year=2024):
    """
    Check if a specific scheme and year combination is available.

    Parameters:
    - scheme (str): The reporting scheme name (default: 'CORSIA')
    - year (int): The year to check (default: 2024)

    Returns:
    - bool: True if the scheme and year are available, False otherwise
    """
    return scheme in REGULATORY_DATA and year in REGULATORY_DATA[scheme]
