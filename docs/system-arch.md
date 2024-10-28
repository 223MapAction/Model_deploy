# System Architecture

This document provides an overview of the system architecture for the Map Action project. It outlines the key components and their interactions within the system.

## Overview

The Map Action project is designed to leverage mapping technology and machine learning to address environmental challenges. The system is composed of several key components, each responsible for specific functionalities.

## Key Components

1. **API Layer**:

    - Built using FastAPI, this layer handles incoming requests and routes them to the appropriate services.
    - Key files: `main_router.py`, `image_model.py`.

2. **Services**:

    - **Celery**: Manages asynchronous task processing for operations like image prediction and contextual information retrieval.
        - Key files: `celery_config.py`, `celery_task.py`.
    - **CNN**: Handles image preprocessing and classification using a convolutional neural network.
        - Key files: `cnn_preprocess.py`, `cnn_model.py`, `cnn.py`.
    - **LLM**: Utilizes a language model to generate responses and analyze satellite data.
        - Key files: `llm.py`.

3. **Database**:

    - Stores prediction results, chat history, and other relevant data.
    - Interacts with the API layer for data retrieval and storage.

4. **External Integrations**:
    - **OpenAI API**: Used by the LLM component for generating responses.
    - **Redis**: Serves as the message broker and backend for Celery.

## Interaction Flow

1. A request is received by the API layer, which validates and processes the input data.
2. The request is routed to the appropriate service, such as the CNN for image classification or the LLM for generating responses.
3. Asynchronous tasks are managed by Celery, allowing for efficient processing and response generation.
4. Results are stored in the database and can be retrieved for further analysis or reporting.

This architecture ensures a scalable and efficient system capable of handling complex environmental data and providing actionable insights.

For more detailed information on each component, refer to the respective documentation files in the `docs/` directory.
