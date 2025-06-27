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
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://nwzsmdbyjmjzhruguwrb.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im53enNtZGJ5am1qemhydWd1d3JiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk2NTU5NDIsImV4cCI6MjA2NTIzMTk0Mn0.QV6VF7Sx1XqHMnxrpgfWLFOdSaDT1xrCcbFIbqak93g')
SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'images')


def upload_file_to_supabase(file_data: bytes, file_name: str, bucket: str = None, content_type: str = 'image/png') -> Optional[str]:
    """
    Upload a file to Supabase Storage and return the public URL.

    Args:
        file_data (bytes): The binary content of the file to upload.
        file_name (str): The name/path for the file in storage.
        bucket (str, optional): The bucket name. Defaults to SUPABASE_BUCKET.
        content_type (str): The MIME type of the file. Defaults to 'image/png'.

    Returns:
        Optional[str]: The public URL of the uploaded file, or None if upload failed.
    """
    if bucket is None:
        bucket = SUPABASE_BUCKET

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
            # Generate public URL
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{unique_file_name}"
            logger.info(f"File uploaded successfully: {public_url}")
            return public_url
        else:
            logger.error(f"Failed to upload file to Supabase. Status: {response.status_code}, Response: {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error uploading file to Supabase: {str(e)}")
        return None


def upload_plot_to_supabase(plot_data: bytes, plot_type: str, incident_id: str = None) -> Optional[str]:
    """
    Upload a plot/chart to Supabase Storage with standardized naming.

    Args:
        plot_data (bytes): The binary content of the plot image.
        plot_type (str): Type of plot (e.g., 'ndvi_ndwi', 'ndvi_heatmap', 'landcover').
        incident_id (str, optional): The incident ID for organizing uploads.

    Returns:
        Optional[str]: The public URL of the uploaded plot, or None if upload failed.
    """
    try:
        # Create standardized filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if incident_id:
            file_name = f"{plot_type}_incident_{incident_id}_{timestamp}.png"
        else:
            file_name = f"{plot_type}_{timestamp}.png"

        return upload_file_to_supabase(plot_data, file_name, content_type='image/png')

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
