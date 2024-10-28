<p align="center">
  <img src="https://dashboard.map-action.com/static/media/logo.ff03b7a9.png" width="100" alt="project-logo">
</p>
<p align="center">
    <h1 align="center">Model_deploy</h1>
</p>
<p align="center">
    <em>FastAPI wrapper for Map Action Model deployment.</em>
</p>
<p align="center">
	<img src="https://img.shields.io/github/license/223MapAction/Model_deploy.git?style=flat-square&amp;logo=opensourceinitiative&amp;logoColor=white&amp;color=0080ff" alt="license">
	<img src="https://img.shields.io/github/last-commit/223MapAction/Model_deploy.git?style=flat-square&amp;logo=git&amp;logoColor=white&amp;color=0080ff" alt="last-commit">
	<img src="https://img.shields.io/github/languages/top/223MapAction/Model_deploy.git?style=flat-square&amp;color=0080ff" alt="repo-top-language">
	<img src="https://img.shields.io/github/languages/count/223MapAction/Model_deploy.git?style=flat-square&amp;color=0080ff" alt="repo-language-count">
<p>
<p align="center">
		<em>Developed with the software and tools below.</em>
</p>
<p align="center">
	<img src="https://img.shields.io/badge/Streamlit-FF4B4B.svg?style=flat-square&amp;logo=Streamlit&amp;logoColor=white" alt="Streamlit">
	<img src="https://img.shields.io/badge/Pydantic-E92063.svg?style=flat-square&amp;logo=Pydantic&amp;logoColor=white" alt="Pydantic">
	<img src="https://img.shields.io/badge/YAML-CB171E.svg?style=flat-square&amp;logo=YAML&amp;logoColor=white" alt="YAML">
	<img src="https://img.shields.io/badge/OpenAI-412991.svg?style=flat-square&amp;logo=OpenAI&amp;logoColor=white" alt="OpenAI">
	<img src="https://img.shields.io/badge/Celery-37814A.svg?style=flat-square&amp;logo=Celery&amp;logoColor=white" alt="Celery">
	<img src="https://img.shields.io/badge/Celery-37814A.svg?style=flat-square&amp;logo=Celery&amp;logoColor=white" alt="Celery">
	<br>
	<img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat-square&amp;logo=Python&amp;logoColor=white" alt="Python">
	<img src="https://img.shields.io/badge/Docker-2496ED.svg?style=flat-square&amp;logo=Docker&amp;logoColor=white" alt="Docker">
	<img src="https://img.shields.io/badge/GitHub%20Actions-2088FF.svg?style=flat-square&amp;logo=GitHub-Actions&amp;logoColor=white" alt="GitHub%20Actions">
	<img src="https://img.shields.io/badge/Pytest-0A9EDC.svg?style=flat-square&amp;logo=Pytest&amp;logoColor=white" alt="Pytest">
	<img src="https://img.shields.io/badge/FastAPI-009688.svg?style=flat-square&amp;logo=FastAPI&amp;logoColor=white" alt="FastAPI">
</p>

<br><!-- TABLE OF CONTENTS -->

<details>
  <summary>Table of Contents</summary><br>

-   [Overview](#overview)
-   [Features](#features)
-   [Repository Structure](#repository-structure)
-   [Modules](#modules)
-   [Getting Started](#getting-started)
    -   [Installation](#installation)
    -   [Usage](#usage)
    -   [Tests](#tests)
-   [Contributing](#contributing)
-   [License](#license)
-   [Acknowledgments](#acknowledgments)
-   [Code of Conduct](#code-of-conduct)
</details>
<hr>

## Overview

Model_deploy is a versatile open-source project designed for seamless deployment and scalable management of machine learning models. Leveraging FastAPI, Celery, and Transformers, it offers robust features such as asynchronous task management, context building, and image classification. With Dockerized environments, CI/CD pipelines, and PostgreSQL integration, Model_deploy ensures efficient ML deployment with enhanced maintainability and scalability. This projects value proposition lies in simplifying ML model deployment processes while enabling reliable and performance-driven AI applications.
[Developper Documentation](https://223mapaction.github.io/Model_deploy/)

---

## System Architecture

The system uses FastAPI endpoints to make predictions using computer vision models and generate summaries using a Large Language Model (LLM).

![System Architecture Diagram](system_arch.png)

---

## How it works

1. The user submits an image through the FastAPI endpoint.
2. The image is processed by a Convolutional Neural Network (CNN) for classification.
3. Based on the CNN output, relevant context is retrieved from the database.
4. The LLM generates a summary using the image classification and retrieved context.
5. The results are returned to the user and stored in the database.

![Workflow Diagram]

---

## Features

|     | Feature              | Description                                                                                                              |
| --- | -------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| ⚙️  | **Architecture**     | Utilizes FastAPI for API creation, Celery for asynchronous tasks, and PostgreSQL for database operations.                |
| 🖼️  | **Image Processing** | Implements CNN-based image classification for environmental issue detection.                                             |
| 🧠  | **LLM Integration**  | Incorporates Large Language Models for context-aware summarization and response generation.                              |
| 🔌  | **Integrations**     | Connects with OpenAI models, uses Redis for Celery task queuing, and implements GitHub Actions for CI/CD.                |
| 🧩  | **Modularity**       | Features a modular codebase with separate services for CNN processing, LLM operations, and API handling.                 |
| 🛡️  | **Security**         | Implements secure practices for handling sensitive information and maintains Docker secrets.                             |
| 📦  | **Dependencies**     | Relies on key libraries including FastAPI, Celery, Transformers, PyTorch, and PostgreSQL for robust ML model deployment. |

---

## Repository Structure

```sh
└── Model_deploy/
    ├── .github
    │   └── workflows
    ├── app
    │   ├── apis
    │   ├── models
    │   └── services
    │       ├── analysis
    │       ├── celery
    │       ├── cnn
    │       ├── llm
    │       └── websockets
    ├── config
    │   └── redis
    ├── cv_model
    ├── docs
    ├── documents
    ├── test
    │   ├── test_apis
    │   ├── test_celery
    │   ├── test_cnn
    │   ├── test_database
    │   ├── test_image_model
    │   └── test_llm
    ├── vector_index
    ├── Dockerfile
    ├── Dockerfile.CI
    ├── Dockerfile.Celery
    ├── LICENSE
    ├── README.md
    ├── ResNet50_TCM1.pth
    ├── _cd_pipeline.yaml
    ├── _ci_pipeline.yml
    ├── mkdocs.yml
    ├── pytest.ini
    ├── requirements.txt
```

This structure highlights the main components of the Model_deploy project:

-   `app/`: Contains the core application code
    -   `apis/`: API endpoints
    -   `models/`: Data models
    -   `services/`: Various services including CNN, LLM, and Celery tasks
-   `config/`: Configuration files
-   `cv_model/`: Computer Vision model files
-   `docs/`: Documentation files
-   `documents/`: Document storage for LLM processing
-   `test/`: Test suites for different components
-   `vector_index/`: Vector storage for LLM
-   Docker-related files for containerization
-   CI/CD pipeline configurations
-   Documentation and licensing files

---

## Modules

<details closed><summary>.</summary>

| File                                                                                                 | Summary                                                                                                                                                                                                                                                                                     |
| ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [requirements.txt](https://github.com/223MapAction/Model_deploy.git/blob/master/requirements.txt)    | Lists Python package dependencies in requirements.txt for seamless project setup and reproducibility. Key libraries include fastapi, celery, transformers, and uvicorn to support ML deployment. Enhances project scalability and maintainability by managing package versions efficiently. |
| [Dockerfile.Celery](https://github.com/223MapAction/Model_deploy.git/blob/master/Dockerfile.Celery)  | Builds a Docker image for Celery worker, leveraging Python 3.10.13, to manage asynchronous tasks in the Model_deploy project. Inherits project dependencies from requirements.txt while ensuring a streamlined environment setup for seamless task execution.                               |
| [Dockerfile](https://github.com/223MapAction/Model_deploy.git/blob/master/Dockerfile)                | Enables deploying a Python application using Uvicorn server, handling data processing requests. Utilizes Docker for portability, installs dependencies, and configures the execution environment. Dynamically serves the app on port 8001 in the container.                                 |
| [Dockerfile.CI](https://github.com/223MapAction/Model_deploy.git/blob/master/Dockerfile.CI)          | Builds Python environment, installs project dependencies, and runs test coverage using pytest in the CI pipeline for Model_deploy.                                                                                                                                                          |
| [\_cd_pipeline.yaml](https://github.com/223MapAction/Model_deploy.git/blob/master/_cd_pipeline.yaml) | Sets up Docker services for a FastAPI app, Redis, and Celery workers with networking configurations in a micro-services environment. Enables communication between services for seamless deployment and scalability.                                                                        |
| [\_ci_pipeline.yml](https://github.com/223MapAction/Model_deploy.git/blob/master/_ci_pipeline.yml)   | Automates creation and configuration of a CI service within the Model_deploy repository. Orchestrates building a Docker container for testing purposes based on the specified Dockerfile.CI. Integrates environment variables for seamless deployment.                                      |

</details>

<details closed><summary>app</summary>

| File                                                                                        | Summary                                                                                                                                                                                                                                                 |
| ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [main.py](https://github.com/223MapAction/Model_deploy.git/blob/master/app/main.py)         | Initializes FastAPI app with CORS middleware.-Connects to the database on app startup.-Gracefully disconnects from the database on app shutdown.-Includes main_routers APIs under /api1 prefix.                                                         |
| [database.py](https://github.com/223MapAction/Model_deploy.git/blob/master/app/database.py) | Establishes a connection to a PostgreSQL database within the Model_deploy repo's app module. Leveraging the databases library, it initializes a database instance with a predefined URL for subsequent data operations across the ML deployment system. |

</details>

<details closed><summary>app.services.llm</summary>

| File                                                                                           | Summary                         |
| ---------------------------------------------------------------------------------------------- | ------------------------------- |
| [llm.py](https://github.com/223MapAction/Model_deploy.git/blob/master/app/services/llm/llm.py) | Contains core LLM functionality |

</details>

<details closed><summary>app.services.cnn</summary>

| File                                                                                                                 | Summary                                                                                                             |
| -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| [cnn_preprocess.py](https://github.com/223MapAction/Model_deploy.git/blob/master/app/services/cnn/cnn_preprocess.py) | Implements image preprocessing for the CNN model, including resizing and normalization.                             |
| [cnn.py](https://github.com/223MapAction/Model_deploy.git/blob/master/app/services/cnn/cnn.py)                       | Contains the main CNN prediction logic, using a pre-trained VGG16 model to classify environmental issues in images. |
| [cnn_model.py](https://github.com/223MapAction/Model_deploy.git/blob/master/app/services/cnn/cnn_model.py)           | Defines the CNN model architecture, adapting VGG16 for the specific classification task.                            |

</details>

<details closed><summary>app.apis</summary>

| File                                                                                                   | Summary                                                                                                                                                                                                                                                                |
| ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [main_router.py](https://github.com/223MapAction/Model_deploy.git/blob/master/app/apis/main_router.py) | Handles image prediction, contextualization, and data insertion. Utilizes FastAPI, requests, and Celery for async tasks. Fetches images, processes predictions, and stores results in the Mapapi_prediction table. Resilient to exceptions with proper error handling. |

</details>

<details closed><summary>app.models</summary>

| File                                                                                                     | Summary                                                                               |
| -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| [image_model.py](https://github.com/223MapAction/Model_deploy.git/blob/master/app/models/image_model.py) | Defines ImageModel with image_name, sensitive_structures, and incident_id attributes. |

</details>

<details closed><summary>test.apis</summary>

| File                                                                                                              | Summary                                                                                                                                            |
| ----------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| [test_main_router.py](https://github.com/223MapAction/Model_deploy.git/blob/master/test/apis/test_main_router.py) | Verifies FastAPI endpoint functionality by simulating HTTP requests to ensure the Index route returns a 200 status code and correct JSON response. |

</details>

<details closed><summary>.github.workflows</summary>

| File                                                                                                  | Summary                                                                                                                                                                                                                                                  |
| ----------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [ci_cd.yml](https://github.com/223MapAction/Model_deploy.git/blob/master/.github/workflows/ci_cd.yml) | Handles continuous integration and deployment via GitHub Actions. Runs test suites to validate code quality, builds and pushes Docker images, and deploys the ML model API on master branch pushes. Includes secret handling for Docker Hub credentials. |

</details>

---

## Getting Started

**System Requirements:**

-   **Python**: `version x.y.z`

### Installation

<h4>From <code>source</code></h4>

> 1. Clone the Model_deploy repository:
>
> ```console
> $ git clone https://github.com/223MapAction/Model_deploy.git
> ```
>
> 2. Change to the project directory:
>
> ```console
> $ cd Model_deploy
> ```
>
> 3. Install the dependencies:
>
> ```console
> $ pip install -r requirements.txt
> ```

### Usage

<h4>From <code>source</code></h4>

> Run Model_deploy using the command below:
>
> ```console
> $ uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
> ```

### Tests

> Run the test suite using the command below:
>
> ```console
> $ pytest --cov=app --cov-report term-missing
> ```

---

## Contributing

Contributions are welcome! Here are several ways you can contribute:

-   **[Report Issues](https://github.com/223MapAction/Model_deploy/issues)**: Submit bugs found or log feature requests for the `Model_deploy` project.
-   **[Submit Pull Requests](https://github.com/223MapAction/Model_deploy/pulls)**: Review open PRs, and submit your own PRs.
-   **[Join the Discussions](https://github.com/223MapAction/Model_deploy/discussions)**: Share your insights, provide feedback, or ask questions.

See our [Contribution Guidelines](https://github.com/223MapAction/.github/blob/main/CONTRIBUTING.md) for details on how to contribute.

<details closed>
<summary>Contributor Graph</summary>
<br>
<p align="center">
   <a href="https://github.com{/223MapAction/Model_deploy.git/}graphs/contributors">
      <img src="https://contrib.rocks/image?repo=223MapAction/Model_deploy.git">
   </a>
</p>
</details>

---

## License

This project is licensed under the [GNU Affero General Public License v3.0](https://choosealicense.com/licenses/agpl-3.0/). For more details, refer to the [LICENSE](https://choosealicense.com/licenses/agpl-3.0/) file.

---

## Acknowledgments

-   List any resources, contributors, inspiration, etc. here.

[**Return**](#-overview)

---

## Code of Conduct

See our [Code of Conduct](https://github.com/223MapAction/.github/blob/main/CODE_OF_CONDUCT.md) for details on expected behavior in our community.

---

## Digital Public Goods Standard Compliance

This project aims to comply with the Digital Public Goods Standard. Below is a summary of our current compliance status:

1. Relevance to Sustainable Development Goals: [Brief explanation]
2. Use of Approved Open License: Compliant (AGPL-3.0 license)
3. Clear Ownership: [Brief explanation]
4. Platform Independence: [Brief explanation]
5. Documentation: Largely compliant (see README and [link to developer docs])
6. Mechanism for Extracting Data: [Brief explanation]
7. Adherence to Privacy and Applicable Laws: [Brief explanation]
8. Adherence to Standards & Best Practices: [Brief explanation]
9. Do No Harm Assessment: [Brief explanation]

For a detailed assessment and ongoing compliance efforts, please see our [DPG_ASSESSMENT.md](DPG_ASSESSMENT.md).
