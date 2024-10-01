import os
import pytest
# Adjust the import based on your file structure
from app.services.llm.llm_preprocessing import chain_workflow, ConversationalRetrievalChain


@pytest.fixture
def setup_env_vars(tmp_path):
    # Set up the environment variables needed for the test
    os.environ["OPENAI_KEY"] = "your_openai_api_key_here"
    os.environ["VECTOR_INDEX_PATH"] = str(tmp_path / "vector_index")
    os.environ["DB_PATH"] = str(tmp_path / "vector_index" / "chroma.sqlite3")
    os.environ["DOCUMENTS_PATH"] = "path_to_your_test_document.pdf"

    # Ensure the directory for VECTOR_INDEX_PATH exists
    (tmp_path / "vector_index").mkdir(parents=True, exist_ok=True)

    # Create an empty chroma.sqlite3 file to simulate an existing database
    with open(os.environ["DB_PATH"], 'w') as f:
        f.write('')

    yield

    # Clean up by unsetting the environment variables
    del os.environ["OPENAI_KEY"]
    del os.environ["VECTOR_INDEX_PATH"]
    del os.environ["DB_PATH"]
    del os.environ["DOCUMENTS_PATH"]


def test_chain_workflow_real(setup_env_vars):
    openai_api_key = os.getenv("OPENAI_KEY")

    # Run the function
    qa_chain = chain_workflow(openai_api_key)

    # Check the type of the output
    assert isinstance(
        qa_chain, ConversationalRetrievalChain), "Output is not a ConversationalRetrievalChain"


if __name__ == '__main__':
    pytest.main()
