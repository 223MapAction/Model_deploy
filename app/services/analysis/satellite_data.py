import os
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import datetime
from dotenv import load_dotenv
import rasterio
import numpy as np
from rasterio.warp import reproject, Resampling

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
    Preprocess Sentinel data using rasterio instead of SNAP.
    """
    with rasterio.open(input_file) as src:
        # Read the required bands (assuming B2, B3, B4, B8 are indices 1, 2, 3, 7)
        band_indices = [1, 2, 3, 7]
        data = src.read(band_indices)
        
        # Get the metadata
        profile = src.profile
        
        # Update the profile for the output
        profile.update(
            count=len(band_indices),
            dtype=rasterio.float32,
            nodata=None
        )
        
        # Perform resampling to 10m resolution (assuming original resolution is 10m)
        data_resampled = np.zeros((len(band_indices), src.height, src.width), dtype=np.float32)
        for i, band in enumerate(data):
            reproject(
                band,
                data_resampled[i],
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=src.transform,
                dst_crs=src.crs,
                resampling=Resampling.bilinear
            )
        
        # Write the result
        with rasterio.open(output_file, 'w', **profile) as dst:
            dst.write(data_resampled)
    
    return output_file
