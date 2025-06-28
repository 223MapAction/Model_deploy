"""
Supabase Storage Service for uploading files to Supabase storage buckets.
"""

import os
import logging
import requests
import uuid
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'images')


def upload_file_to_supabase(file_data: bytes, file_name: str, bucket: str = None, content_type: str = 'image/png') -> Optional[str]:
    """
    Upload a file to Supabase Storage and return a signed URL.

    Args:
        file_data (bytes): The binary content of the file to upload.
        file_name (str): The name/path for the file in storage.
        bucket (str, optional): The bucket name. Defaults to SUPABASE_BUCKET.
        content_type (str): The MIME type of the file. Defaults to 'image/png'.

    Returns:
        Optional[str]: The signed URL of the uploaded file, or None if upload failed.
    """
    if bucket is None:
        bucket = SUPABASE_BUCKET

    # Add fallback defaults if environment variables are missing
    if not SUPABASE_URL or SUPABASE_URL == 'None':
        logger.error("SUPABASE_URL is not set or is 'None'")
        return None
    
    if not SUPABASE_KEY or SUPABASE_KEY == 'None':
        logger.error("SUPABASE_KEY is not set or is 'None'")
        return None

    try:
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        unique_file_name = f"plots/{timestamp}_{unique_id}_{file_name}"

        # Supabase Storage API endpoint
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{unique_file_name}"

        # Headers for authentication
        headers = {
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': content_type,
            'Cache-Control': '3600',
            'upsert': 'false'
        }

        # Upload the file
        logger.info(f"Uploading file to Supabase: {unique_file_name}")
        response = requests.post(upload_url, data=file_data, headers=headers)

        if response.status_code in [200, 201]:
            # Create a signed URL instead of returning the public URL
            signed_url = create_signed_url(unique_file_name, bucket, expires_in=3600*24*7)  # 7 days expiry
            if signed_url:
                logger.info(f"File uploaded successfully with signed URL: {unique_file_name}")
                return signed_url
            else:
                logger.error(f"File uploaded but failed to create signed URL for: {unique_file_name}")
                return None
        else:
            logger.error(f"Failed to upload file to Supabase. Status: {response.status_code}, Response: {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error uploading file to Supabase: {str(e)}")
        return None


def upload_plot_to_supabase(plot_data, plot_type: str, incident_id: str = None) -> Optional[str]:
    """
    Upload a plot/chart to Supabase Storage with standardized naming.

    Args:
        plot_data: Either bytes data or a file path string.
        plot_type (str): Type of plot (e.g., 'ndvi_ndwi', 'ndvi_heatmap', 'landcover').
        incident_id (str, optional): The incident ID for organizing uploads.

    Returns:
        Optional[str]: The signed URL of the uploaded plot, or None if upload failed.
    """
    file_path_to_delete = None  # Track file path for cleanup
    
    try:
        # Handle both bytes data and file paths
        if isinstance(plot_data, str):
            # It's a file path, read the file
            file_path_to_delete = plot_data  # Remember to delete this file later
            try:
                with open(plot_data, 'rb') as file:
                    file_bytes = file.read()
                logger.info(f"Read plot file from path: {plot_data}")
            except Exception as e:
                logger.error(f"Failed to read plot file from path {plot_data}: {str(e)}")
                return None
        elif isinstance(plot_data, bytes):
            # It's already bytes data
            file_bytes = plot_data
        else:
            logger.error(f"Invalid plot_data type: {type(plot_data)}. Expected str (file path) or bytes.")
            return None

        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if incident_id:
            file_name = f"{plot_type}_incident_{incident_id}_{timestamp}.png"
        else:
            file_name = f"{plot_type}_{timestamp}.png"
        
        # Upload the file
        upload_result = upload_file_to_supabase(file_bytes, file_name, content_type='image/png')
        
        # If upload was successful and we have a file to delete, clean it up
        if upload_result and file_path_to_delete:
            try:
                os.remove(file_path_to_delete)
                logger.info(f"Deleted local file after successful upload: {file_path_to_delete}")
            except OSError as e:
                logger.error(f"Error deleting local file {file_path_to_delete}: {e}")
                # Continue even if deletion fails, as upload was successful
        
        return upload_result
    except Exception as e:
        logger.error(f"Error uploading plot to Supabase: {str(e)}")
        return None


def create_signed_url(file_path: str, bucket: str = None, expires_in: int = 3600) -> Optional[str]:
    """
    Create a signed URL for accessing a file in Supabase Storage.

    Args:
        file_path (str): The path to the file in storage.
        bucket (str, optional): The bucket name. Defaults to SUPABASE_BUCKET.  
        expires_in (int): Expiration time in seconds. Defaults to 3600 (1 hour).

    Returns:
        Optional[str]: The signed URL, or None if creation failed.
    """
    if bucket is None:
        bucket = SUPABASE_BUCKET

    # Add fallback defaults if environment variables are missing
    if not SUPABASE_URL or SUPABASE_URL == 'None':
        logger.error("SUPABASE_URL is not set or is 'None'")
        return None
    
    if not SUPABASE_KEY or SUPABASE_KEY == 'None':
        logger.error("SUPABASE_KEY is not set or is 'None'")
        return None

    try:
        # Supabase Storage API endpoint for creating signed URLs
        signed_url_endpoint = f"{SUPABASE_URL}/storage/v1/object/sign/{bucket}/{file_path}"

        headers = {
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }

        payload = {
            'expiresIn': expires_in
        }

        response = requests.post(signed_url_endpoint, json=payload, headers=headers)

        if response.status_code == 200:
            signed_data = response.json()
            signed_url = f"{SUPABASE_URL}/storage/v1{signed_data['signedURL']}"
            logger.info(f"Signed URL created successfully for {file_path}")
            return signed_url
        else:
            logger.error(f"Failed to create signed URL. Status: {response.status_code}, Response: {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error creating signed URL: {str(e)}")
        return None
