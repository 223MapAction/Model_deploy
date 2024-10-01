import pytest
from celery import Celery
from app.services.celery.celery_config import make_celery, celery_app


def test_make_celery():
    # Call the function to get the Celery instance
    celery = make_celery()

    # Verify the type of the returned instance
    assert isinstance(celery, Celery)

    # Verify the backend and broker URLs
    expected_backend = 'redis://yugo:Maoene@redis:6379/0'
    expected_broker = 'redis://yugo:Maoene@redis:6379/0'

    assert celery.conf.result_backend == expected_backend
    assert celery.conf.broker_url == expected_broker


def test_celery_app():
    # Verify the celery_app instance
    assert isinstance(celery_app, Celery)

    # Verify the backend and broker URLs
    expected_backend = 'redis://yugo:Maoene@redis:6379/0'
    expected_broker = 'redis://yugo:Maoene@redis:6379/0'

    assert celery_app.conf.result_backend == expected_backend
    assert celery_app.conf.broker_url == expected_broker


if __name__ == "__main__":
    pytest.main()
