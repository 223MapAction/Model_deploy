import os
import uuid
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient

# Initialize the BlobServiceClient
account_url = os.environ['BLOB_ACCOUNT_URL']
default_credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(account_url, credential=default_credential)

def upload_image_to_blob(container_name: str, image_data: bytes) -> str:
    """
    Uploads an image to Azure Blob Storage and returns the URL of the uploaded blob with a SAS token.

    :param container_name: The name of the container to upload the image to.
    :param image_data: The binary data of the image to upload.
    :return: The URL of the uploaded blob with a SAS token.
    """
    # Create a unique name for the blob using a UUID
    blob_name = f"{uuid.uuid4()}.png"

    # Create a blob client
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    # Upload the image
    blob_client.upload_blob(image_data)

    # Retrieve the SAS token from an environment variable
    sas_token = os.environ.get('BLOB_SAS_TOKEN', '')

    # Append the SAS token to the URL
    url_with_sas = f"{blob_client.url}?{sas_token}"

    # Return the URL of the uploaded blob with the SAS token
    return url_with_sas
