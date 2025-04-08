import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define empty functions as fallbacks
def dummy_analyze(*args, **kwargs):
    logger.warning("Analysis function called but dependencies are not available")
    return None, None

def dummy_generate(*args, **kwargs):
    logger.warning("Plot generation function called but dependencies are not available")
    return None

# Try to import the actual functions, but fall back to dummies if they're not available
try:
    from .incident_analysis import analyze_vegetation_and_water, analyze_land_cover, generate_ndvi_ndwi_plot, generate_ndvi_heatmap, generate_landcover_plot
    logger.info("Successfully imported analysis functions")
except ImportError as e:
    logger.warning(f"Failed to import analysis functions: {e}")
    # Set up fallbacks
    analyze_vegetation_and_water = dummy_analyze
    analyze_land_cover = dummy_analyze
    generate_ndvi_ndwi_plot = dummy_generate
    generate_ndvi_heatmap = dummy_generate
    generate_landcover_plot = dummy_generate