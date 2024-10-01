import os
import pytest
from app.services.llm.gpt_3_5_turbo import get_response, display_chat_history, messages


def test_display_chat_history(capsys):
    test_messages = [
        {"role": "assistant", "content": "Comment puis-je vous assister?"},
        {"role": "user", "content": "Quel temps fait-il aujourd'hui?"},
    ]
    display_chat_history(test_messages)
    captured = capsys.readouterr()
    assert "Assistant: Comment puis-je vous assister?" in captured.out
    assert "User: Quel temps fait-il aujourd'hui?" in captured.out


def test_get_assistant_response_real():
    prompt = "Quel temps fait-il aujourd'hui?"
    response = get_response(prompt)

    # Check if the response is a non-empty string
    assert isinstance(response, str)
    assert len(response) > 0

    # Check if the chat history was updated correctly
    assert messages[-2] == {"role": "user", "content": prompt}
    assert messages[-1]["role"] == "assistant"
    assert isinstance(messages[-1]["content"], str)


if __name__ == '__main__':
    pytest.main()
