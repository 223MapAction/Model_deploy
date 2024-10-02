# import pytest
# from unittest.mock import patch, MagicMock
# import torch
# from app.services.celery.celery_task import perform_prediction, fetch_contextual_information


# @pytest.fixture
# def mock_predict():
#     with patch('app.services.celery.celery_task.predict') as mock:
#         yield mock


# @pytest.fixture
# def mock_get_response():
#     with patch('app.services.celery.celery_task.get_response') as mock:
#         yield mock


# def test_perform_prediction(mock_predict):
#     # Setup mock
#     mock_predict.return_value = ("cat", torch.tensor([0.1, 0.9]))

#     # Call the task
#     image_data = b"fake_image_data"
#     result = perform_prediction(image_data)

#     # Assertions
#     assert result[0] == "cat"
#     assert result[1] == pytest.approx([0.1, 0.9], rel=1e-5)
#     mock_predict.assert_called_once_with(image_data)


# def test_fetch_contextual_information(mock_get_response):
#     # Setup mock
#     mock_get_response.side_effect = [
#         "A cat in an African zone",
#         "Impact of cat on sensitive structures",
#         "Possible solutions for managing the cat in the community"
#     ]

#     # Call the task
#     prediction = "cat"
#     sensitive_structures = ["structure1", "structure2"]
#     result = fetch_contextual_information(prediction, sensitive_structures)

#     # Assertions
#     assert result == (
#         "A cat in an African zone",
#         "Impact of cat on sensitive structures",
#         "Possible solutions for managing the cat in the community"
#     )
#     assert mock_get_response.call_count == 3
#     mock_get_response.assert_any_call("What is a cat in an African zone?")
#     mock_get_response.assert_any_call(
#         "What is the impact of cat on ['structure1', 'structure2']")
#     mock_get_response.assert_any_call(
#         "What are the possible solutions for the previous case? Assuming it's managed by a local community.")


# if __name__ == "__main__":
#     pytest.main()
