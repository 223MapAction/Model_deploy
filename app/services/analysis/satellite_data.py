import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def download_sentinel_data(area_of_interest_geojson, start_date, end_date, output_dir):
    """
    Download Sentinel-2 data for the area of interest and time range using the Copernicus Data Space Ecosystem APIs.

    :param area_of_interest_geojson: Path to a GeoJSON file defining the area of interest
    :param start_date: Start date for the search (format: 'YYYYMMDD')
    :param end_date: End date for the search (format: 'YYYYMMDD')
    :param output_dir: Directory to save the downloaded data
    :return: List of paths to downloaded files
    """
    # Client credentials
    client_id = os.environ.get('COPERNICUS_CLIENT_ID')
    client_secret = os.environ.get('COPERNICUS_CLIENT_SECRET')

    if not client_id or not client_secret:
        raise ValueError("Copernicus API credentials not found. Please set COPERNICUS_CLIENT_ID and COPERNICUS_CLIENT_SECRET environment variables.")

    # Authenticate and get an access token
    token_url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }

    try:
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        access_token = token_response.json()['access_token']
    except Exception as e:
        print(f"Error fetching access token: {e}")
        return []

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Read and parse the area of interest from the GeoJSON file
    with open(area_of_interest_geojson, 'r') as f:
        geojson_data = json.load(f)

    # Extract the geometry object
    if 'features' in geojson_data and len(geojson_data['features']) > 0:
        area_of_interest = geojson_data['features'][0]['geometry']
    elif 'geometry' in geojson_data:
        area_of_interest = geojson_data['geometry']
    else:
        raise ValueError("Invalid GeoJSON format. Cannot find 'geometry'.")

    # Convert dates to ISO format
    start_date_iso = datetime.strptime(start_date, '%Y%m%d').isoformat() + 'Z'
    end_date_iso = datetime.strptime(end_date, '%Y%m%d').isoformat() + 'Z'

    # STAC API search endpoint
    search_url = 'https://catalogue.dataspace.copernicus.eu/stac/search'

    # Search parameters
    search_params = {
        "datetime": f"{start_date_iso}/{end_date_iso}",
        "collections": ["sentinel-2-l2a"],  # Updated collection ID
        "limit": 10,
        "intersects": area_of_interest,
        "query": {
            "eo:cloud_cover": {
                "lt": 30
            }
        }
    }

    try:
        response = requests.post(search_url, json=search_params, headers=headers)
        response.raise_for_status()
        search_results = response.json()
    except Exception as e:
        print(f"Error searching for products: {e}")
        print(f"Response status code: {response.status_code}")
        print(f"Response text: {response.text}")
        return []

    if not search_results.get('features'):
        print("No products found for the given criteria.")
        return []

    # Download the products
    downloaded_files = []
    for feature in search_results['features']:
        product_id = feature['id']
        download_url = feature['assets']['download']['href']

        # Some products may require authentication even for download
        try:
            # Stream download to avoid loading the entire file into memory
            with requests.get(download_url, headers=headers, stream=True) as r:
                r.raise_for_status()
                output_file = os.path.join(output_dir, f"{product_id}.zip")
                with open(output_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                downloaded_files.append(output_file)
                print(f"Downloaded: {output_file}")
        except Exception as e:
            print(f"Error downloading product {product_id}: {e}")

    return downloaded_files
