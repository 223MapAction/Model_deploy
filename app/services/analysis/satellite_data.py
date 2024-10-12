import os
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import datetime
from dotenv import load_dotenv
import rasterio
import numpy as np

# Load environment variables
load_dotenv()

def download_sentinel_data(area_of_interest, start_date, end_date, output_dir):
    """
    Download Sentinel-2 data for the area of interest and time range using the Sentinel API.

    :param area_of_interest: Path to a GeoJSON file defining the area of interest
    :param start_date: Start date for the search (format: 'YYYYMMDD')
    :param end_date: End date for the search (format: 'YYYYMMDD')
    :param output_dir: Directory to save the downloaded data
    :return: List of paths to downloaded files
    """
    # Sentinel API credentials
    user = os.environ.get('COPERNICUS_CLIENT_ID')
    password = os.environ.get('COPERNICUS_CLIENT_SECRET')

    if not user or not password:
        raise ValueError("Copernicus API credentials not found. Please set COPERNICUS_CLIENT_ID and COPERNICUS_CLIENT_SECRET environment variables.")

    # Initialize the API with the correct endpoint
    api = SentinelAPI(user, password, 'https://apihub.copernicus.eu/apihub')

    # Convert dates to datetime objects
    start_date = datetime.strptime(start_date, '%Y%m%d')
    end_date = datetime.strptime(end_date, '%Y%m%d')

    # Read the area of interest from the GeoJSON file
    footprint = geojson_to_wkt(read_geojson(area_of_interest))

    # Search for Sentinel-2 products
    products = api.query(
        footprint,
        date=(start_date, end_date),
        platformname='Sentinel-2',
        processinglevel='Level-2A',  # Level-2A products (surface reflectance)
        cloudcoverpercentage=(0, 30)  # Max 30% cloud cover
    )

    if not products:
        print("No products found for the given criteria.")
        return []

    # Download all found products
    downloaded_files = []
    for product_id, product_info in products.items():
        try:
            # Download the product
            result = api.download(product_id, directory_path=output_dir)
            downloaded_files.append(result['path'])
            print(f"Downloaded: {result['path']}")
        except Exception as e:
            print(f"Error downloading product {product_id}: {str(e)}")

    return downloaded_files

def preprocess_sentinel_data(input_zip_file, output_file):
    """
    Preprocess Sentinel-2 Level-2A data using rasterio.

    :param input_zip_file: Path to the downloaded Sentinel-2 zip file
    :param output_file: Path to save the preprocessed output file
    :return: Path to the preprocessed output file
    """
    import zipfile

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
        granule_ids = set()
        for filename in zip_list:
            if 'GRANULE/' in filename and filename.endswith('/'):
                parts = filename.split('/')
                granule_index = parts.index('GRANULE') + 1
                granule_id = parts[granule_index]
                granule_ids.add(granule_id)

        if not granule_ids:
            raise ValueError("No GRANULE folder found in the input file.")

        # Use the first granule if multiple are found
        granule_id = list(granule_ids)[0]

        # Build the base path to the 10m bands
        base_path = None
        for filename in zip_list:
            if f'GRANULE/{granule_id}/IMG_DATA/R10m/' in filename:
                base_path = f'GRANULE/{granule_id}/IMG_DATA/R10m/'
                break

        if not base_path:
            raise ValueError("No R10m folder found in the input file.")

        # Find the JP2 files for the required bands
        for band_name in bands.keys():
            for filename in zip_list:
                if filename.startswith(base_path) and filename.endswith(f'{band_name}_10m.jp2'):
                    bands[band_name] = filename
                    break

        # Check if all bands were found
        if None in bands.values():
            missing_bands = [k for k, v in bands.items() if v is None]
            raise ValueError(f"Not all required bands were found in the input file. Missing bands: {missing_bands}")

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
        with rasterio.open(output_file, 'w', **profile) as dst:
            dst.write(data_array.astype(rasterio.float32))

    return output_file

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
    for input_file in downloaded_files:
        output_file = os.path.join(output_dir, os.path.basename(input_file).replace('.zip', '_processed.tif'))
        preprocess_sentinel_data(input_file, output_file)
        print(f"Preprocessed file saved to: {output_file}")
