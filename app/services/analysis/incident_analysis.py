import os
import rasterio
import numpy as np
from scipy import ndimage
import logging
from .satellite_data import preprocess_sentinel_data, download_sentinel_data
from shapely.geometry import Point
import geopandas as gpd
import requests

def analyze_incident_zone(incident_location, incident_type, start_date, end_date) -> np.ndarray:
    """
    Analyze the incident zone using satellite data.

    Returns:
    np.ndarray: A boolean mask where True values indicate the impact area.
    """
    logging.info(f"Analyzing incident zone for {incident_type} at {incident_location}")
    
    # Create output directory for Sentinel data
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'sentinel_data')
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert incident_location to a GeoJSON file
    area_of_interest = create_geojson_from_location(incident_location, output_dir)
    
    try:
        # Download and preprocess Sentinel data
        raw_data_files = download_sentinel_data(area_of_interest, start_date, end_date, output_dir)
        processed_data_files = preprocess_sentinel_data(raw_data_files, output_dir)
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download Sentinel data: {str(e)}")
        raise ValueError("Unable to access Sentinel data. The data source may have changed. Please update the data retrieval method.")
    
    if not processed_data_files:
        logging.error("No processed data files available for analysis.")
        raise ValueError("No data available for analysis after preprocessing.")

    # For simplicity, we'll use the first processed file. In a real scenario, you might want to analyze all files or merge them.
    processed_data = processed_data_files[0]
    
    # Read the processed data
    with rasterio.open(processed_data) as src:
        satellite_image = src.read()
    
    logging.info(f"Satellite image shape: {satellite_image.shape}")
    
    # Perform analysis based on incident type
    if incident_type == 'Caniveau obstrué':
        impact_area = analyze_blocked_drain(satellite_image)
    elif incident_type == 'Déchet dans l\'eau':
        impact_area = analyze_water_waste(satellite_image)
    elif incident_type == 'Déchet solide':
        impact_area = analyze_solid_waste(satellite_image)
    elif incident_type == 'Déforestation':
        impact_area = analyze_deforestation(satellite_image)
    elif incident_type == 'Pollution de l\'eau':
        impact_area = analyze_water_pollution(satellite_image)
    elif incident_type == 'Sécheresse':
        impact_area = analyze_drought(satellite_image)
    elif incident_type == 'Sol dégradé':
        impact_area = analyze_soil_degradation(satellite_image)
    else:
        logging.error(f"Unsupported incident type: {incident_type}")
        raise ValueError(f"Unsupported incident type: {incident_type}")
    
    logging.info(f"Impact area shape: {impact_area.shape}, non-zero elements: {np.count_nonzero(impact_area)}")
    return impact_area

def analyze_flood_extent(satellite_image):
    """
    Analyze flood extent using NDWI (Normalized Difference Water Index).
    """
    green_band = satellite_image[1]
    nir_band = satellite_image[3]
    
    ndwi = (green_band - nir_band) / (green_band + nir_band)
    flood_mask = ndwi > 0.3  # Adjust threshold as needed
    
    return flood_mask

def analyze_burn_area(satellite_image):
    """
    Analyze burn area using NBR (Normalized Burn Ratio).
    """
    nir_band = satellite_image[3]
    swir_band = satellite_image[4]  # Assuming band 5 is SWIR
    
    nbr = (nir_band - swir_band) / (nir_band + swir_band)
    burn_mask = nbr < -0.2  # Adjust threshold as needed
    
    return burn_mask

def analyze_blocked_drain(satellite_image):
    """
    Analyze blocked drains using satellite imagery.
    """
    logging.info("Analyzing blocked drains")
    # Use NDWI to identify water bodies
    green_band = satellite_image[1]
    nir_band = satellite_image[3]
    
    ndwi = (green_band - nir_band) / (green_band + nir_band)
    water_mask = ndwi > 0.2
    
    # Look for unusual patterns in water bodies that might indicate blockages
    labeled_water, num_features = ndimage.label(water_mask)
    sizes = ndimage.sum(water_mask, labeled_water, range(1, num_features + 1))
    mask_size = sizes < 100  # Adjust threshold as needed
    blocked_drain_mask = mask_size[labeled_water - 1]
    
    logging.info(f"Blocked drain analysis complete. Found {np.count_nonzero(blocked_drain_mask)} potential blockages")
    return blocked_drain_mask

def analyze_water_waste(satellite_image):
    """
    Analyze waste in water using satellite imagery.
    """
    # Use a combination of NDWI and turbidity analysis
    green_band = satellite_image[1]
    red_band = satellite_image[2]
    nir_band = satellite_image[3]
    
    ndwi = (green_band - nir_band) / (green_band + nir_band)
    water_mask = ndwi > 0.2
    
    # Calculate turbidity (simplified)
    turbidity = red_band / green_band
    high_turbidity = turbidity > 1.5  # Adjust threshold as needed
    
    waste_in_water_mask = water_mask & high_turbidity
    return waste_in_water_mask

def analyze_solid_waste(satellite_image):
    """
    Analyze solid waste using satellite imagery.
    """
    # Use spectral indices to identify areas with abnormal reflectance
    red_band = satellite_image[2]
    nir_band = satellite_image[3]
    swir_band = satellite_image[4]
    
    ndvi = (nir_band - red_band) / (nir_band + red_band)
    nbr = (nir_band - swir_band) / (nir_band + swir_band)
    
    potential_waste_mask = (ndvi < 0.1) & (nbr < 0)  # Adjust thresholds as needed
    return potential_waste_mask

def analyze_deforestation(satellite_image):
    """
    Analyze deforestation using satellite imagery.
    """
    # Use NDVI to identify vegetation loss
    red_band = satellite_image[2]
    nir_band = satellite_image[3]
    
    ndvi = (nir_band - red_band) / (nir_band + red_band)
    vegetation_mask = ndvi > 0.4
    
    # Compare with historical NDVI data (assuming we have access to it)
    historical_ndvi = 0.6  # This should be calculated from historical data
    deforestation_mask = (historical_ndvi - ndvi) > 0.2  # Adjust threshold as needed
    
    return deforestation_mask

def analyze_water_pollution(satellite_image):
    """
    Analyze water pollution using satellite imagery.
    """
    # Use a combination of NDWI and color analysis
    blue_band = satellite_image[0]
    green_band = satellite_image[1]
    red_band = satellite_image[2]
    nir_band = satellite_image[3]
    
    ndwi = (green_band - nir_band) / (green_band + nir_band)
    water_mask = ndwi > 0.2
    
    # Analyze water color (simplified)
    blue_green_ratio = blue_band / green_band
    polluted_water_mask = (blue_green_ratio < 0.8) & water_mask  # Adjust threshold as needed
    
    return polluted_water_mask

def analyze_drought(satellite_image):
    """
    Analyze drought conditions using satellite imagery.
    """
    # Use NDVI and land surface temperature (if available)
    red_band = satellite_image[2]
    nir_band = satellite_image[3]
    
    ndvi = (nir_band - red_band) / (nir_band + red_band)
    drought_mask = ndvi < 0.2  # Adjust threshold as needed
    
    # If thermal band is available, incorporate land surface temperature
    if len(satellite_image) > 5:
        thermal_band = satellite_image[5]
        high_temp_mask = thermal_band > 40  # Adjust threshold as needed (in Celsius)
        drought_mask = drought_mask & high_temp_mask
    
    return drought_mask

def analyze_soil_degradation(satellite_image):
    """
    Analyze soil degradation using satellite imagery.
    """
    logging.info("Analyzing soil degradation")
    # Use a combination of NDVI and soil-adjusted vegetation index (SAVI)
    red_band = satellite_image[2]
    nir_band = satellite_image[3]
    
    ndvi = (nir_band - red_band) / (nir_band + red_band)
    
    # SAVI calculation
    L = 0.5  # soil brightness correction factor
    savi = ((nir_band - red_band) / (nir_band + red_band + L)) * (1 + L)
    
    # Identify areas with low vegetation and potentially degraded soil
    degraded_soil_mask = (ndvi < 0.2) & (savi < 0.3)  # Adjust thresholds as needed
    
    logging.info(f"Soil degradation analysis complete. Degraded area: {np.count_nonzero(degraded_soil_mask)} pixels")
    return degraded_soil_mask

def create_geojson_from_location(location, output_dir):
    """
    Create a GeoJSON file from a location string (assuming it's a point location).
    
    :param location: String representing a location (e.g., "Bambilor")
    :param output_dir: Directory to save the GeoJSON file
    :return: Path to the created GeoJSON file
    """
    # For simplicity, we're using a dummy coordinate. In a real-world scenario,
    # you'd use a geocoding service to get the actual coordinates.
    point = Point(0, 0)
    gdf = gpd.GeoDataFrame({'name': [location]}, geometry=[point], crs="EPSG:4326")
    
    geojson_path = os.path.join(output_dir, f"{location}.geojson")
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    return geojson_path
