# import unittest
# from unittest.mock import patch, MagicMock
# import torch
# from app.services.cnn.cnn import predict, categories


# class TestPredictFunction(unittest.TestCase):

#     @patch('app.services.cnn.cnn.preprocess_image')
#     @patch('app.services.cnn.cnn.model')
#     def test_predict(self, mock_model, mock_preprocess_image):
#         # Mocking the preprocess_image function to return a tensor
#         mock_preprocess_image.return_value = torch.randn(
#             1, 3, 224, 224)  # Example shape for VGG16 input

#         # Mocking the model's output
#         mock_output = torch.randn(1, len(categories))  # Example output tensor
#         mock_model.eval = MagicMock()
#         mock_model.__call__ = MagicMock(return_value=mock_output)

#         # Mocking softmax function to control the output probabilities
#         with patch('torch.nn.functional.softmax', return_value=torch.tensor([0.1, 0.2, 0.15, 0.05, 0.4, 0.1])):
#             # Input image data (bytes)
#             image_data = b'test image data'

#             # Call the predict function
#             predicted_label, probabilities = predict(image_data)

#             # Assertions to check if the predict function returns expected results
#             # Index 4 corresponds to the highest probability 0.4
#             self.assertEqual(predicted_label, categories[4])
#             self.assertEqual(len(probabilities), len(categories))
#             # Probabilities should sum to 1
#             self.assertAlmostEqual(sum(probabilities), 1.0, places=5)


# if __name__ == '__main__':
#     unittest.main()
