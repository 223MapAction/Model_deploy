import pytest
from unittest.mock import patch
from app.services.celery import celery_config
def test_broker_url():
    assert celery_config.broker_url == 'redis://localhost:6379/0'

def test_result_backend():
    assert celery_config.result_backend == 'redis://localhost:6379/0'

def test_task_serializer():
    assert celery_config.task_serializer == 'json'

def test_result_serializer():
    assert celery_config.result_serializer == 'json'

def test_accept_content():
    assert celery_config.accept_content == ['json']

@pytest.mark.parametrize("env,expected", [
    ('development', 'INFO'),
    ('production', 'WARNING'),
])
def test_log_level(env, expected):
    with patch('os.environ.get', return_value=env):
        assert celery_config.log_level == expected

@patch('celery.schedules.crontab')
def test_beat_schedule(mock_crontab):
    mock_crontab.return_value = 'mocked_crontab'
    expected_schedule = {
        'sample_task': {
            'task': 'your_project.tasks.sample_task',
            'schedule': 'mocked_crontab',
        }
    }
    assert celery_config.beat_schedule == expected_schedule
    mock_crontab.assert_called_once_with(minute='0', hour='0')

def test_task_routes():
    expected_routes = {
        'your_project.tasks.*': {'queue': 'default'},
    }
    assert celery_config.task_routes == expected_routes
