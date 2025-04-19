# -*- coding: utf-8 -*-
"""
Retrieves NIH funding information for a specified Principal Investigator (PI)
using the NIH RePORTER API v2.

This script prompts the user for the PI's first and last name, queries the API,
and prints details ONLY for currently active or future grants (where the
project end date is later than the current date). Details include grant number,
award amount, and project start/end dates.
"""
import csv
import requests
import json
from datetime import datetime, date

# API endpoint for project search
API_URL = "https://api.reporter.nih.gov/v2/projects/search"

# Headers for the API request
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def format_date(date_str):
    """
    Formats a date string from 'YYYY-MM-DDTHH:mm:ssZ' to 'MM/DD/YYYY'.
    Returns the original string if formatting fails or input is None.
    """
    if not date_str:
        return "N/A"
    try:
        # Parse the date string (ignoring the time part)
        dt_obj = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d')
        return dt_obj.strftime('%m/%d/%Y')
    except ValueError:
        print(f"Warning: Could not parse date '{date_str}'. Displaying original.")
        return date_str # Return original if format is unexpected

def format_currency(amount):
    """
    Formats an integer amount into a currency string (e.g., $1,234,567).
    Returns "N/A" if the amount is None or invalid.
    """
    if amount is None:
        return "N/A"
    try:
        return f"${amount:,.0f}"
    except (ValueError, TypeError):
        return "N/A"

def get_nih_funding(first_name, last_name, limit=50):
    """
    Fetches NIH funding data for a given PI name.

    Args:
        first_name (str): The first name of the Principal Investigator.
        last_name (str): The last name of the Principal Investigator.
        limit (int): The maximum number of records to retrieve (default 50).
                     Note: The API might have its own maximum limit per request.

    Returns:
        list: A list of dictionaries, where each dictionary contains details
              of a funded project. Returns an empty list if no projects are found
              or an error occurs.
    """
    print(f"\nSearching for NIH grants for PI: {first_name} {last_name}...")

    # Construct the payload for the API request
    payload = {
        "criteria": {
            "pi_names": [
                {
                    "first_name": first_name,
                    "last_name": last_name,
                }
            ]
        },
        "include_fields": [
            "ProjectNum",       # Grant Number
            "AwardAmount",      # Funding Amount for the specific year/record
            "ProjectStartDate", # Start Date of the Project
            "ProjectEndDate",   # End Date of the Project
            "BudgetStart",      # Specific budget period start <--- ADD THIS
            "BudgetEnd",        # Specific budget period end   <--- ADD THIS
            "ContactPiName",    # PI Name for verification
            "ProjectTitle",     # Title of the project
            "Organization",     # Awardee institution details
            "FiscalYear"        # Fiscal Year of the specific record
        ],
        "offset": 0,
        "limit": limit,
        "sort_field": "fiscal_year", # Sort by fiscal year
        "sort_order": "desc"         # Show most recent first
    }

    try:
        # Send the POST request to the API
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)

        # Check if the request was successful
        response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        # Check if 'results' key exists and has data
        if "results" in data and data["results"]:
            print(f"Found {len(data['results'])} grant records (limit was {limit}). Filtering for active grants...")
            return data["results"]
        else:
            print("No matching NIH grant records found.")
            return []

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the API request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                print("API Error Details:", json.dumps(error_details, indent=2))
            except json.JSONDecodeError:
                print("Could not parse error response from API.")
                print("API Response Text:", e.response.text)
        return []
    except json.JSONDecodeError:
        print("Error decoding the JSON response from the API.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

def display_funding_info(funding_data):
    """
    Filters and displays the funding information for active grants.

    Args:
        funding_data (list): A list of project dictionaries from the API.
    """
    if not funding_data:
        return # Nothing to display

    today = date.today() # Get today's date for comparison
    one_year_ago = today.replace(year=today.year - 1) # Get the date one year ago
    # create a cutoff date of 2026-01-01
    cutoff_date = date(2026, 1, 1) # Set a cutoff date for filtering
    active_grants = []

    # list of grants that are returned from the methods

    grant_list = []

    # Filter grants based on ProjectEndDate
    for grant in funding_data:
        budget_start_str = grant.get("budget_start")
        budget_end_str = grant.get("budget_end")
        end_date_str = grant.get("project_end_date",'2020-01-01T12:00:00Z') # Default to a past date if not found
        if end_date_str:
            try:
                # Parse only the date part (YYYY-MM-DD)
                budget_end_date = datetime.strptime(budget_end_str.split('T')[0], '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str.split('T')[0], '%Y-%m-%d').date()  # Ensure end_date is parsed
                # Keep the grant if its budget start date is today or later and end date is after cutoff
                if budget_end_date > today and end_date >= cutoff_date:
                    active_grants.append(grant)
            except ValueError:
                # Handle cases where the date format might be unexpected
                print(f"Warning: Could not parse end date '{end_date_str}' for grant {grant.get('project_num', 'N/A')}. Skipping filter for this grant.")
                # Optionally, you could decide to include/exclude grants with unparseable dates
        else:
            # Handle cases where ProjectEndDate is missing
             print(f"Warning: Missing end date for grant {grant.get('project_num', 'N/A')}. Skipping filter for this grant.")
             # Optionally, include/exclude based on your preference for missing dates

    # Check if any active grants were found after filtering
    if not active_grants:
        print("\nNo active or future grants found matching the criteria.")
        return

    print(f"\n--- Active NIH Funding Details ({len(active_grants)} found) ---")
    for grant in active_grants:
        # Extract data, providing defaults if keys are missing
        grant_num = grant.get("project_num", "N/A")
        pi_name = grant.get("contact_pi_name", "N/A")
        title = grant.get("project_title", "N/A")
        amount = grant.get("award_amount") # Keep as number for formatting
        start_date_str = grant.get("project_start_date")
        end_date_str = grant.get("project_end_date")
        fy = grant.get("fiscal_year", "N/A")
        org_name = grant.get("organization", {}).get("org_name", "N/A")
        # Extract budget period dates
        budget_start_str = grant.get("budget_start") # Note: API response keys might be snake_case
        budget_end_str = grant.get("budget_end")     # e.g., budget_start_date, budget_end_date

        # Format dates and amount
        start_date = format_date(start_date_str)
        end_date = format_date(end_date_str) # Format the end date for display
        formatted_amount = format_currency(amount)

        # Format dates using the existing function
        budget_start = format_date(budget_start_str)
        budget_end = format_date(budget_end_str)

        # store the datat into a dictionary
        grant_dict = {
            "grant_num": grant_num,
            "pi_name": pi_name,
            "title": title,
            "org_name": org_name,
            "fy": fy,
            "award_amount": formatted_amount,
            "start_date": start_date,
            "end_date": end_date,
            "budget_start": budget_start,
            "budget_end": budget_end
        }
        grant_list.append(grant_dict) # Append the dictionary to the list
        # Print details for each grant record
        print("-" * 25)
        print(f"Grant Number: {grant_num}")
        print(f"PI Name:      {pi_name}")
        print(f"Title:        {title}")
        print(f"Institution:  {org_name}")
        print(f"Fiscal Year:  {fy}")
        print(f"Award Amount: {formatted_amount} (for FY {fy})")
        print(f"Project Start:{start_date}")
        print(f"Project End:  {end_date}") # Display the end date

    print("\n--- End of Active Details ---")
    print("\nNote: Award amounts shown are typically for the specific fiscal year listed.")
    print("Only grants with an end date after today are shown.")
    return grant_list # Return the list of grants for further processing if needed

if __name__ == "__main__":
    print("NIH Active Funding Lookup Tool")
    print("==============================")

    # # Get PI name from user input
    # while True:
    #     first_name_input = input("Enter the PI's First Name: ").strip()
    #     if first_name_input:
    #         break
    #     else:
    #         print("First name cannot be empty.")

    # while True:
    #     last_name_input = input("Enter the PI's Last Name: ").strip()
    #     if last_name_input:
    #         break
    #     else:
    #         print("Last name cannot be empty.")

    # # Fetch and display the funding data
    # grants = get_nih_funding(first_name_input, last_name_input)
    # display_funding_info(grants) # This function now filters and displays

    # print("\nScript finished.")

piList = [('al’Absi', 'Mustafa'), ('Anker', 'Justin'), ('Bishop', 'Jeffrey'), ('Carroll', 'Dana'), ('Conelea', 'Christine'), ('Fair', 'Damien'), ('Gunlicks-Stoessel', 'Meredith'), ('Krueger', 'Robert'), ('Kummerfeld', 'Erich'), ('Kushner', 'Matt'), ('Lim', 'Kelvin'), ('Luciana', 'Monica'), ('McGue', 'Matthew'), ('McMorris', 'Barbara'), ('Peterson', 'Carol'), ('Piehler', 'Timothy'), ('Redish', 'A. David'), ('Rinehart', 'Linda'), ('Schallmo', 'Michael-Paul'), ('Specker', 'Sheila'), ('Sponheim', 'Scott'), ('Thomas', 'Mark'), ('Toomey', 'Traci'), ('Vrieze', 'Scott'), ('Widome', 'Rachel'), ('Wilson', 'Sylia')]

# read the piList from a csv file
with open('unique_names.csv', 'r') as f:
    # ignore the header row
    next(f)
    reader = csv.reader(f)
    piList = list(reader)

# Initialize an empty list to store grant data

# iterate through the list of tuples and call the function for each PI
for pi in piList:
    last_name, first_name = pi
    print(f"\nFetching funding information for {first_name} {last_name}...")
    grants = get_nih_funding(first_name, last_name)
    grant_list = display_funding_info(grants) # This function now filters and displays
    # concatenate the list of dictionaries into a single list

    if 'grant_lists' not in locals():
        grant_lists = grant_list
    else:
        if grant_list:
            # Check if grant_list is not empty before extending
            # concatenate the list of dictionaries into a single list   
            grant_lists.extend(grant_list)

# write the list of dictionaries to a csv file
import pandas as pd


df = pd.DataFrame(grant_lists)


csv_file_name = 'nih_grant_funding.csv'


df.to_csv(csv_file_name, index=False)

print(f"Grant funding information has been written to {csv_file_name}.")

pass