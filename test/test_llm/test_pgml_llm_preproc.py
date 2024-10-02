# import os
# import pytest
# import asyncio
# from unittest.mock import patch, MagicMock, AsyncMock
# from app.services.llm.pgml_llm_preprocessing import chat_flow


# @pytest.fixture
# def setup_env_vars():
#     # Set up the necessary environment variables and file paths
#     os.environ["PGML_CONNINFO"] = "postgres://root:postgresml@localhost:5433/postgresml"
#     os.environ["DOCUMENTS_PATH"] = "/Users/babawhizzo/Code/map_action_ml/ML-Deploy/test/test_llm/dummy.pdf"

#     yield

#     # Clean up by unsetting the environment variables
#     del os.environ["PGML_CONNINFO"]
#     del os.environ["DOCUMENTS_PATH"]


# @pytest.mark.asyncio
# @patch("app.services.llm.pgml_llm_preprocessing.Collection")
# @patch("app.services.llm.pgml_llm_preprocessing.Pipeline")
# async def test_chat_flow(mock_Pipeline, mock_Collection, setup_env_vars):
#     # Mock the Pipeline and Collection objects
#     mock_pipeline_instance = MagicMock()
#     mock_Pipeline.return_value = mock_pipeline_instance

#     mock_collection_instance = MagicMock()
#     mock_Collection.return_value = mock_collection_instance
#     mock_collection_instance.add_pipeline = AsyncMock()
#     mock_collection_instance.upsert_documents = AsyncMock()

#     # Call the chat_flow function
#     collection, pipeline = await chat_flow()

#     # Assertions to verify the behavior
#     mock_Pipeline.assert_called_once_with(
#         "Main_Pipeline",
#         {
#             "body": {
#                 "splitter": {"model": "recursive_character"},
#                 "semantic_search": {
#                     "model": "hkunlp/instructor-base",
#                     "parameters": {
#                         "instruction": "Represent the Wikipedia document for retrieval: ",
#                     },
#                 },
#             },
#         },
#     )
#     mock_Collection.assert_called_once_with(
#         "MapActionManifesto", "postgres://root:postgresml@localhost:5433/postgresml")
#     mock_collection_instance.add_pipeline.assert_called_once_with(
#         mock_pipeline_instance)
#     mock_collection_instance.upsert_documents.assert_called_once()

# if __name__ == '__main__':
#     pytest.main()
