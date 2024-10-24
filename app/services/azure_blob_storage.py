import os
import uuid
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient

# Initialize the BlobServiceClient
account_url = os.environ['BLOB_ACCOUNT_URL']
default_credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(account_url, credential=default_credential)

def upload_file_to_blob(container_name: str, file_path: str) -> str:
    """
    Uploads a file to Azure Blob Storage and returns the URL of the uploaded blob.
    After uploading, the file is deleted from its original location.

    :param container_name: The name of the container to upload the file to.
    :param file_path: The path to the file to upload.
    :return: The URL of the uploaded blob.
    """
    # Use the existing filename from the file path
    blob_name = os.path.basename(file_path)

    # Create a blob client
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    # Read the file and upload it as a binary stream
    with open(file_path, 'rb') as file_data:
        blob_client.upload_blob(file_data, blob_type="BlockBlob", overwrite=True)

    # Delete the file after uploading
    os.remove(file_path)

    # Return the URL of the uploaded blob
    return blob_client.url
