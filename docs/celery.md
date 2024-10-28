# Celery Configuration and Tasks

This document provides an overview of the Celery configuration and tasks used in the Map Action project. Celery is used for distributed task processing, allowing for efficient handling of asynchronous operations.

## Celery Configuration

The Celery application is configured in the `celery_config.py` file. It uses Redis as both the message broker and backend for task queueing and result storage. The configuration retrieves Redis connection details from environment variables.

### Key Components

-   **Redis**: Used as the message broker and backend for Celery.
-   **Environment Variables**: `REDIS_HOST`, `REDIS_PORT`, `REDIS_USERNAME`, `REDIS_PASSWORD`, and `REDIS_URL` are used to configure the Redis connection.

## Celery Tasks

The Celery tasks are defined in the `celery_task.py` file. These tasks perform various operations, including image prediction, fetching contextual information, and analyzing incident zones.

### Tasks Overview

-   **perform_prediction**: Uses a convolutional neural network to predict the content of an image and calculate classification probabilities.
-   **fetch_contextual_information**: Fetches contextual information based on the prediction, sensitive structures, and geographic zone.
-   **analyze_incident_zone**: Analyzes the incident zone using satellite data, generating analysis results and plot data.

### Task Details

-   **perform_prediction**:

    -   **Args**: `image` (bytes) - The image data to be processed.
    -   **Returns**: A tuple containing the predicted classification and probabilities.

-   **fetch_contextual_information**:

    -   **Args**: `prediction` (str), `sensitive_structures` (list), `zone` (str).
    -   **Returns**: A tuple containing analysis and piste_solution, both formatted in markdown.

-   **analyze_incident_zone**:
    -   **Args**: `lat` (float), `lon` (float), `incident_location` (str), `incident_type` (str), `start_date` (str), `end_date` (str).
    -   **Returns**: A dictionary containing analysis results and plot data.

For more detailed information on each task, refer to the `celery_task.py` file in the `app/services/celery/` directory.
