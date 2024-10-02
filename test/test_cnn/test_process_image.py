# import pytest
# import torch
# from PIL import Image
# import io
# from app.services.cnn.cnn_preprocess import preprocess_image


# def create_dummy_image_bytes():
#     """
#     Creates a dummy image in bytes format for testing purposes.
#     """
#     img = Image.new('RGB', (100, 100), color='red')  # Create a red dummy image
#     img_byte_arr = io.BytesIO()
#     img.save(img_byte_arr, format='PNG')
#     return img_byte_arr.getvalue()


# def test_preprocess_image():
#     # Create dummy image bytes
#     dummy_image_bytes = create_dummy_image_bytes()

#     # Call preprocess_image with the dummy image
#     processed_image_tensor = preprocess_image(dummy_image_bytes)

#     # Check the type of the output
#     assert isinstance(processed_image_tensor,
#                       torch.Tensor), "Output is not a tensor"

#     # Check the shape of the output tensor
#     assert processed_image_tensor.shape == (
#         1, 3, 224, 224), "Output tensor shape is incorrect"

#     # Check if the values are within the expected range for image data
#     assert processed_image_tensor.min() >= 0.0 and processed_image_tensor.max(
#     ) <= 1.0, "Tensor values are out of expected range (0.0 to 1.0)"


# if __name__ == '__main__':
#     pytest.main()
