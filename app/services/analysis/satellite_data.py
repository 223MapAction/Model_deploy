import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import json
import numpy as np
import logging
import rasterio
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.error("Copernicus API credentials not found. Please set COPERNICUS_CLIENT_ID and COPERNICUS_CLIENT_SECRET environment variables.")
        raise ValueError("Copernicus API credentials not found.")

    # Create a client and an OAuth2 session
    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)

    # Define a compliance hook to handle server errors correctly
    def sentinelhub_compliance_hook(response):
        response.raise_for_status()
        return response

    oauth.register_compliance_hook("access_token_response", sentinelhub_compliance_hook)

    # Fetch an access token using the client credentials grant
    token_url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
    try:
        token = oauth.fetch_token(
            token_url=token_url,
            client_id=client_id,
            client_secret=client_secret,
            include_client_id=True
        )
        logger.info("Access token obtained.")
    except Exception as e:
        logger.error(f"Error fetching token: {e}")
        return []

    # Read and parse the area of interest from the GeoJSON file
    try:
        with open(area_of_interest_geojson, 'r') as f:
            geojson_data = json.load(f)

        # Extract the geometry object
        if 'features' in geojson_data and len(geojson_data['features']) > 0:
            geometry = geojson_data['features'][0]['geometry']
        elif 'geometry' in geojson_data:
            geometry = geojson_data['geometry']
        else:
            raise ValueError("Invalid GeoJSON format. Cannot find 'geometry'.")
        
        # Calculate bounding box from geometry
        if geometry['type'] == 'Point':
            lon, lat = geometry['coordinates']
            delta = 0.1  # Increase this value to create a larger bounding box
            bbox = [lon - delta, lat - delta, lon + delta, lat + delta]
        elif geometry['type'] == 'Polygon':
            coordinates = geometry['coordinates'][0]
            lons, lats = zip(*coordinates)
            bbox = [min(lons), min(lats), max(lons), max(lats)]
        else:
            raise ValueError(f"Unsupported geometry type: {geometry['type']}")
    except Exception as e:
        logger.error(f"Error reading or parsing GeoJSON file: {e}")
        raise ValueError(f"Invalid GeoJSON file: {str(e)}")

    # Convert dates to ISO format
    start_date_iso = datetime.strptime(start_date, '%Y%m%d').isoformat() + 'Z'
    end_date_iso = datetime.strptime(end_date, '%Y%m%d').isoformat() + 'Z'

    # STAC API search endpoint
    search_url = 'https://catalogue.dataspace.copernicus.eu/stac/search'

    # Search parameters
    search_params = {
        "bbox": bbox,
        "datetime": f"{start_date_iso}/{end_date_iso}",
        "collections": ["SENTINEL-2"],
        "limit": 10,
        "filter": {
            "op": "<",
            "args": [
                {"property": "cloudCover"},  # Changed from "eo:cloud_cover" to "cloudCover"
                30
            ]
        },
        "filter-lang": "cql2-json"
    }

    # Add more logging
    logger.info(f"Searching for Sentinel data with parameters: bbox={bbox}, start_date={start_date_iso}, end_date={end_date_iso}")
    logger.info(f"Search parameters: {json.dumps(search_params, indent=2)}")

    try:
        response = oauth.post(search_url, json=search_params)
        response.raise_for_status()
        search_results = response.json()
        logger.info(f"Search results: {json.dumps(search_results, indent=2)}")
    except Exception as e:
        logger.error(f"Error searching for products: {e}")
        logger.error(f"Response status code: {response.status_code}")
        logger.error(f"Response text: {response.text}")
        return []

    if not search_results.get('features'):
        logger.info("No products found for the given criteria.")
        return []

    # Download the products
    downloaded_files = []
    for feature in search_results['features']:
        product_id = feature['id']
        download_url = feature['assets']['download']['href']

        try:
            # Stream download to avoid loading the entire file into memory
            with oauth.get(download_url, stream=True) as r:
                r.raise_for_status()
                output_file = os.path.join(output_dir, f"{product_id}.zip")
                with open(output_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                downloaded_files.append(output_file)
                logger.info(f"Downloaded: {output_file}")
        except Exception as e:
            logger.error(f"Error downloading product {product_id}: {e}")

    return downloaded_files


def preprocess_sentinel_data(input_files, output_dir):
    """
    Preprocess Sentinel-2 Level-2A data using rasterio.

    This function takes a list of downloaded Sentinel-2 zip files, extracts the required
    bands (Blue, Green, Red, and NIR), and combines them into a single multi-band GeoTIFF file.

    :param input_files: List of paths to the downloaded Sentinel-2 zip files
    :param output_dir: Directory to save the preprocessed output files
    :return: List of paths to the preprocessed output files (GeoTIFF)

    The function performs the following steps for each input file:
    1. Extracts the required bands (B02, B03, B04, B08) from the zip file
    2. Stacks these bands into a single 4-band array
    3. Saves the result as a GeoTIFF file in the output directory

    If any errors occur during processing (e.g., missing bands), the function will log a warning
    and skip that file, continuing with the next one.

    Note: This function requires the 'rasterio' library to be installed.
    """
    import rasterio
    import zipfile

    preprocessed_files = []

    for input_zip_file in input_files:
        # Bands of interest and their filenames
        bands = {
            'B02': None,  # Blue
            'B03': None,  # Green
            'B04': None,  # Red
            'B08': None   # NIR
        }

        # Open the zip file
        with zipfile.ZipFile(input_zip_file, 'r') as z:
            # List all files in the zip
            zip_list = z.namelist()

            # Find the granule IDs
            granule_paths = [name for name in zip_list if 'GRANULE' in name and name.endswith('.jp2')]

            if not granule_paths:
                logger.warning(f"No GRANULE files found in {input_zip_file}. Skipping this file.")
                continue

            # Find the JP2 files for the required bands
            for band_name in bands.keys():
                for filename in granule_paths:
                    if f'_{band_name}_' in filename:
                        bands[band_name] = filename
                        break

            # Check if all bands were found
            if None in bands.values():
                missing_bands = [k for k, v in bands.items() if v is None]
                logger.warning(f"Not all required bands were found in {input_zip_file}. Missing bands: {missing_bands}. Skipping this file.")
                continue

            # Read the bands using rasterio
            band_data = []
            profile = None
            for band_name, band_path in bands.items():
                with rasterio.open(f'/vsizip/{input_zip_file}/{band_path}') as src:
                    band_data.append(src.read(1))
                    # Save profile for later use
                    if profile is None:
                        profile = src.profile

            # Stack bands into a single array
            data_array = np.stack(band_data)

            # Update profile
            profile.update(
                count=len(band_data),
                dtype=rasterio.float32,
                nodata=None
            )

            # Write the result
            output_file = os.path.join(output_dir, os.path.basename(input_zip_file).replace('.zip', '_processed.tif'))
            with rasterio.open(output_file, 'w', **profile) as dst:
                dst.write(data_array.astype(rasterio.float32))

            preprocessed_files.append(output_file)
            logger.info(f"Preprocessed file saved to: {output_file}")

    return preprocessed_files


# Example usage:
if __name__ == "__main__":
    # Define parameters
    area_of_interest = 'path_to_your_geojson_file.geojson'  # Replace with your GeoJSON file path
    start_date = '20230101'  # Start date in 'YYYYMMDD' format
    end_date = '20231012'    # End date in 'YYYYMMDD' format
    output_dir = 'path_to_output_directory'  # Replace with your desired output directory

    # Download Sentinel-2 data
    downloaded_files = download_sentinel_data(area_of_interest, start_date, end_date, output_dir)

    # Preprocess the downloaded data
    preprocessed_files = preprocess_sentinel_data(downloaded_files, output_dir)
    print(f"Preprocessed files saved to: {preprocessed_files}")
