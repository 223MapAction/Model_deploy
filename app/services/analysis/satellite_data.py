import snappy
from snappy import ProductIO, GPF
import os
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def download_sentinel_data(area_of_interest, start_date, end_date, output_dir):
    """
    Download Sentinel data for the area of interest and time range using the Copernicus Open Access Hub API.
    
    :param area_of_interest: Path to a GeoJSON file defining the area of interest
    :param start_date: Start date for the search (format: 'YYYYMMDD')
    :param end_date: End date for the search (format: 'YYYYMMDD')
    :param output_dir: Directory to save the downloaded data
    :return: List of paths to downloaded files
    """
    # Copernicus Open Access Hub credentials
    user = os.environ.get('COPERNICUS_USERNAME')
    password = os.environ.get('COPERNICUS_PASSWORD')
    
    if not user or not password:
        raise ValueError("Copernicus Open Access Hub credentials not found. Please set COPERNICUS_USERNAME and COPERNICUS_PASSWORD environment variables.")

    # Initialize the API
    api = SentinelAPI(user, password, 'https://scihub.copernicus.eu/dhus')

    # Convert dates to datetime objects
    start_date = datetime.strptime(start_date, '%Y%m%d')
    end_date = datetime.strptime(end_date, '%Y%m%d')

    # Read the area of interest from the GeoJSON file
    footprint = geojson_to_wkt(read_geojson(area_of_interest))

    # Search for Sentinel-2 products
    products = api.query(footprint,
                         date=(start_date, end_date),
                         platformname='Sentinel-2',
                         producttype='S2MSI2A',  # Level-2A products (surface reflectance)
                         cloudcoverpercentage=(0, 30))  # Max 30% cloud cover

    if not products:
        print("No products found for the given criteria.")
        return []

    # Download all found products
    downloaded_files = []
    for product_id, product_info in products.items():
        try:
            # Download the product
            download_path = api.download(product_id, directory_path=output_dir)
            downloaded_files.append(download_path)
            print(f"Downloaded: {download_path}")
        except Exception as e:
            print(f"Error downloading product {product_id}: {str(e)}")

    return downloaded_files

def preprocess_sentinel_data(input_file, output_file):
    """
    Preprocess Sentinel data using SNAP.
    """
    # Read the source product
    source_product = ProductIO.readProduct(input_file)
    
    # Define processing parameters
    parameters = snappy.HashMap()
    parameters.put('sourceBands', 'B2,B3,B4,B8')
    parameters.put('resamplingType', 'Bilinear')
    
    # Apply preprocessing
    result = GPF.createProduct("Resample", parameters, source_product)
    
    # Write the result
    ProductIO.writeProduct(result, output_file, 'GeoTIFF')
    
    return output_file
