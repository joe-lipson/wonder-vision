import sys
import pandas as pd
import requests
import re
import urllib.parse
import time
import argparse

###
# Reads a list of taxa from an excel file and makes iNat API calls to
# check if there are obervations and if they have a vision model or not
# usage: python wonder-vision.py -f <excel file>

###
# make an API call to iNat to get the taxon id
def get_taxon_id(species):
    url_encoded_species = urllib.parse.quote(species)
    url = f"https://api.inaturalist.org/v1/observations?taxon_id=&taxon_name={url_encoded_species}&per_page=1&order=desc&order_by=created_at"
    header = {"Accept": "application/json"}
    pause = 0

    response = requests.get(url, headers=header)

    # retry if we're being rate limited
    while response.status_code == 429:
        pause = pause + 2
        print(f"## Requests are being rate limited, waiting and retrying in {pause} seconds")
        time.sleep(pause)
        response = requests.get(url, headers=header)
        if pause > 30:
            break

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        json_response = response.json()
        if json_response['total_results'] > 0:
            taxon_id = json_response['results'][0]['taxon']['min_species_taxon_id']
        else:
            taxon_id = None
    else:
        print("Request failed with status code:", response.status_code)
        taxon_id = None

    return (taxon_id)

###
# API call to iNat to get the vision field for a taxa
def get_vision(taxa_id):
    url = f"https://api.inaturalist.org/v1/taxa/{taxa_id}"
    header = {"Accept": "application/json"}
    pause = 0

    response = requests.get(url, headers=header)

    # retry if we're being rate limited
    while response.status_code == 429:
        pause = pause + 2
        print(f"## Requests are being rate limited, waiting and retrying in {pause} seconds")
        time.sleep(pause)
        response = requests.get(url, headers=header)
        if pause > 30:
            break

    if response.status_code == 200:
        # Parse the JSON response
        json_response = response.json()
        vision = json_response['results'][0]['vision']
    else:
        print("Request failed with status code:", response.status_code)
        vision = None

    return (vision)

##################################


# get cmd line args
parser = argparse.ArgumentParser()
parser.add_argument("--excel-file", "-f",
                    help="Excel input file", required=True)
args = parser.parse_args()

# Load the Excel file and go to the first sheet
df = pd.read_excel(args.excel_file, sheet_name=0)

# Read the first column
first_column = df.iloc[:, 0]

# go through the values line by line
for species in first_column:
    # strip brackets and whitespace
    species = re.sub(r'\([^)]*\)', '', species).strip()

    taxon_id = get_taxon_id(species)
    if taxon_id:
        vision = get_vision(taxon_id)
        print(f"{species} vision: {vision}")
    else:
        print(f"{species}: no observations")
