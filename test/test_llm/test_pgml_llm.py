import pytest

from app.services.llm.pgml_llm import build_history_with_context


def test_build_history_with_context():
    context = "test context"
    expected_history = [
        {"role": "system", "content": "You're an AI assistant"}]

    result = build_history_with_context(context)

    assert result == expected_history, f"Expected {expected_history}, but got {result}"


if __name__ == "__main__":
    pytest.main()
