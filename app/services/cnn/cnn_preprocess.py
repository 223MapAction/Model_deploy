import io
from PIL import Image
from torchvision.transforms import transforms

# Define a transformation sequence for preprocessing images
transform = transforms.Compose([
    transforms.Resize((224, 224)),  # Resize the input image to 224x224 pixels
    transforms.ToTensor(),          # Convert the image to a PyTorch tensor
    # Uncomment the following line to normalize the image
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def preprocess_image(image):
    """
    Preprocesses an image for model prediction by resizing, converting it to a tensor, 
    and potentially normalizing it. This function is specifically tailored for models 
    that expect input images of size 224x224 pixels and images in tensor format.

    Args:
        image (bytes): The image data in bytes format, as received from an image file or a network.

    Returns:
        torch.Tensor: A PyTorch tensor representing the processed image, ready to be fed into a model.
                      The tensor is unsqueezed, adding a batch dimension at the beginning.
    """
    image = Image.open(io.BytesIO(image)).convert("RGB")  # Open and convert image to RGB
    image = transform(image).unsqueeze(0)  # Apply the transformation and add a batch dimension
    return image
