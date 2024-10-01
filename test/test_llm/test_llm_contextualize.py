import os
import pytest
from app.services.llm.llm import contextualize


@pytest.fixture
def setup_env_vars(tmp_path):
    # Set up the environment variables needed for the test
    os.environ["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]
    os.environ["VECTOR_INDEX_PATH"] = str(tmp_path / "vector_index")
    os.environ["DB_PATH"] = str(tmp_path / "vector_index" / "chroma.sqlite3")
    os.environ["DOCUMENTS_PATH"] = "/Users/babawhizzo/Code/map_action_ml/ML-Deploy/test/test_llm/dummy.pdf"

    # Ensure the directory for VECTOR_INDEX_PATH exists
    (tmp_path / "vector_index").mkdir(parents=True, exist_ok=True)

    yield

    # Clean up by unsetting the environment variables
    del os.environ["OPENAI_API_KEY"]
    del os.environ["VECTOR_INDEX_PATH"]
    del os.environ["DB_PATH"]
    del os.environ["DOCUMENTS_PATH"]


def test_contextualize_real(setup_env_vars):
    query = "Quel temps fait-il aujourd'hui?"

    # Call the contextualize function
    response = contextualize(query)

    # Check if the response is a non-empty string
    assert isinstance(response, str)
    assert len(response) > 0


if __name__ == '__main__':
    pytest.main()
