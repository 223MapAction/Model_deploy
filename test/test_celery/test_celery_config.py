import os
from unittest.mock import patch
from app.services.celery.celery_config import make_celery

def test_make_celery():
    with patch.dict(os.environ, {'REDIS_URL': 'redis://testhost:6379'}):
        celery_app = make_celery()
        assert celery_app.conf.broker_url == 'redis://testhost:6379'
        assert celery_app.conf.result_backend == 'redis://testhost:6379'

def test_broker_url():
    with patch.dict(os.environ, {'REDIS_URL': 'redis://testhost:6379'}):
        celery_app = make_celery()
        assert celery_app.conf.broker_url == 'redis://testhost:6379'

def test_result_backend():
    with patch.dict(os.environ, {'REDIS_URL': 'redis://testhost:6379'}):
        celery_app = make_celery()
        assert celery_app.conf.result_backend == 'redis://testhost:6379'

def test_task_serializer():
    celery_app = make_celery()
    assert celery_app.conf.task_serializer == 'json'

def test_result_serializer():
    celery_app = make_celery()
    assert celery_app.conf.result_serializer == 'json'

# def test_accept_content():
#     celery_app = make_celery()
#     assert celery_app.conf.accept_content == ['json']

def test_redis_url_from_env():
    with patch.dict(os.environ, {'REDIS_URL': 'redis://customhost:1234'}):
        celery_app = make_celery()
        assert celery_app.conf.broker_url == 'redis://customhost:1234'
        assert celery_app.conf.result_backend == 'redis://customhost:1234'