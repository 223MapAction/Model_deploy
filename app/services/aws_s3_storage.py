import os
import logging
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_file_to_s3(bucket_name: str, file_path: str, region_name: str = None) -> str | None:
    """
    Uploads a file to AWS S3 and returns the URL of the uploaded object.
    After uploading, the file is deleted from its original location.

    Credentials are automatically sourced from environment variables (AWS_ACCESS_KEY_ID, 
    AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN), shared credential file (~/.aws/credentials), 
    AWS config file (~/.aws/config), or IAM role attached to the EC2 instance/ECS task.

    :param bucket_name: The name of the S3 bucket to upload the file to.
    :param file_path: The path to the file to upload.
    :param region_name: The AWS region where the bucket is located. If None, tries to determine from environment or config.
    :return: The URL of the uploaded S3 object, or None if upload fails.
    """
    if not bucket_name:
        logger.error("S3_BUCKET_NAME environment variable not set.")
        return None
        
    # Determine region
    effective_region = region_name or os.environ.get('AWS_REGION') or boto3.Session().region_name
    if not effective_region:
        logger.warning("AWS region could not be determined. S3 URL might be incorrect or operations might fail if not us-east-1.")
        # Defaulting, but this might not be correct for all buckets
        effective_region = 'us-east-1' 

    # Extract the base filename to use as the S3 object key
    object_key = os.path.basename(file_path)

    # Create an S3 client
    s3_client = boto3.client('s3', region_name=effective_region)

    try:
        # Upload the file
        logger.info(f"Uploading {file_path} to S3 bucket {bucket_name} as {object_key}")
        with open(file_path, 'rb') as file_data:
            s3_client.upload_fileobj(file_data, bucket_name, object_key)
        logger.info(f"Successfully uploaded {object_key} to {bucket_name}")

        # Delete the local file after successful upload
        try:
            os.remove(file_path)
            logger.info(f"Deleted local file: {file_path}")
        except OSError as e:
            logger.error(f"Error deleting local file {file_path}: {e}")
            # Continue even if deletion fails, as upload was successful

        # Construct the S3 object URL
        # Handle different S3 URL formats depending on the region
        if effective_region == 'us-east-1':
            s3_url = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"
        else:
            s3_url = f"https://{bucket_name}.s3.{effective_region}.amazonaws.com/{object_key}"
            
        return s3_url

    except (NoCredentialsError, PartialCredentialsError):
        logger.error("AWS credentials not found. Configure credentials via environment variables, credential file, or IAM role.")
        return None
    except ClientError as e:
        logger.error(f"Failed to upload {file_path} to S3: {e}")
        # Check for specific errors like BucketNotFound
        error_code = e.response.get('Error', {}).get('Code')
        if error_code == 'NoSuchBucket':
             logger.error(f"Bucket '{bucket_name}' does not exist or you don't have permission to access it.")
        return None
    except FileNotFoundError:
        logger.error(f"Local file not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during S3 upload: {e}")
        return None

# Example usage (for testing purposes)
# if __name__ == '__main__':
#     # Create a dummy file
#     dummy_file = "test_upload.txt"
#     with open(dummy_file, "w") as f:
#         f.write("This is a test file.")
# 
#     # Set environment variables (replace with your actual values or ensure they are set)
#     os.environ['S3_BUCKET_NAME'] = 'your-test-bucket-name' 
#     os.environ['AWS_REGION'] = 'your-bucket-region' 
#     # Ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set if not using IAM roles/profiles
# 
#     bucket = os.environ.get('S3_BUCKET_NAME')
#     region = os.environ.get('AWS_REGION')
# 
#     if bucket:
#         uploaded_url = upload_file_to_s3(bucket, dummy_file, region)
#         if uploaded_url:
#             print(f"File uploaded to: {uploaded_url}")
#         else:
#             print("Upload failed.")
#             # Clean up dummy file if it still exists
#             if os.path.exists(dummy_file):
#                 os.remove(dummy_file)
#     else:
#         print("S3_BUCKET_NAME environment variable not set.") 