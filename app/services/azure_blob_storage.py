import os
import uuid
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient

# Initialize the BlobServiceClient
account_url = os.environ['BLOB_ACCOUNT_URL']
default_credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(account_url, credential=default_credential)

def upload_image_to_blob(container_name: str, image_path: str) -> str:
    """
    Uploads an image to Azure Blob Storage and returns the URL of the uploaded blob.

    :param container_name: The name of the container to upload the image to.
    :param image_path: The local path of the image to upload.
    :return: The URL of the uploaded blob.
    """
    # Create a unique name for the blob
    blob_name = str(uuid.uuid4()) + os.path.basename(image_path)

    # Create a blob client
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    # Upload the image
    with open(image_path, "rb") as data:
        blob_client.upload_blob(data)

    # Return the URL of the uploaded blob
    return blob_client.url
