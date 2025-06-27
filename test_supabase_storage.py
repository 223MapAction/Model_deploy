#!/usr/bin/env python3
"""
Test script for Supabase storage functionality.
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.supabase_storage import upload_file_to_supabase, create_signed_url
import io
from PIL import Image

def create_test_image():
    """Create a simple test image."""
    # Create a simple 100x100 test image
    img = Image.new('RGB', (100, 100), color='red')
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    return img_buffer.getvalue()

def test_supabase_upload():
    """Test uploading a file to Supabase storage."""
    print("Testing Supabase storage upload...")
    
    # Create test image data
    test_image_data = create_test_image()
    
    # Test upload
    upload_url = upload_file_to_supabase(
        file_data=test_image_data,
        file_name="test_upload.png",
        bucket="images",
        content_type="image/png"
    )
    
    if upload_url:
        print(f"✅ Upload successful! URL: {upload_url}")
        return upload_url
    else:
        print("❌ Upload failed!")
        return None

def test_signed_url(file_path):
    """Test creating a signed URL."""
    print(f"Testing signed URL creation for: {file_path}")
    
    signed_url = create_signed_url(file_path, bucket="images", expires_in=3600)
    
    if signed_url:
        print(f"✅ Signed URL created: {signed_url}")
        return signed_url
    else:
        print("❌ Signed URL creation failed!")
        return None

if __name__ == "__main__":
    print("🧪 Supabase Storage Test")
    print("=" * 40)
    
    # Test upload
    upload_url = test_supabase_upload()
    
    if upload_url:
        # Extract file path from URL for signed URL test
        file_path = upload_url.split('/')[-1]
        print(f"\nExtracted file path: {file_path}")
        
        # Test signed URL
        signed_url = test_signed_url(f"plots/{file_path}")
    
    print("\n🏁 Test completed!")
