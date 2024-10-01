<p align="center">
  <img src="https://dashboard.map-action.com/static/media/logo.ff03b7a9.png" width="100" alt="project-logo">
</p>
<p align="center">
    <h1 align="center">ML-DEPLOY</h1>
</p>
<p align="center">
    <em>FastAPI wrapper for Map Action Model deployment.</em>
</p>
<p align="center">
	<img src="https://img.shields.io/github/license/223MapAction/ML-Deploy.git?style=flat-square&logo=opensourceinitiative&logoColor=white&color=0080ff" alt="license">
	<img src="https://img.shields.io/github/last-commit/223MapAction/ML-Deploy.git?style=flat-square&logo=git&logoColor=white&color=0080ff" alt="last-commit">
	<img src="https://img.shields.io/github/languages/top/223MapAction/ML-Deploy.git?style=flat-square&color=0080ff" alt="repo-top-language">
	<img src="https://img.shields.io/github/languages/count/223MapAction/ML-Deploy.git?style=flat-square&color=0080ff" alt="repo-language-count">
<p>
<p align="center">
		<em>Developed with the software and tools below.</em>
</p>
<p align="center">
	<img src="https://img.shields.io/badge/Streamlit-FF4B4B.svg?style=flat-square&logo=Streamlit&logoColor=white" alt="Streamlit">
	<img src="https://img.shields.io/badge/Pydantic-E92063.svg?style=flat-square&logo=Pydantic&logoColor=white" alt="Pydantic">
	<img src="https://img.shields.io/badge/YAML-CB171E.svg?style=flat-square&logo=YAML&logoColor=white" alt="YAML">
	<img src="https://img.shields.io/badge/OpenAI-412991.svg?style=flat-square&logo=OpenAI&logoColor=white" alt="OpenAI">
	<img src="https://img.shields.io/badge/Celery-37814A.svg?style=flat-square&logo=Celery&logoColor=white" alt="Celery">
	<img src="https://img.shields.io/badge/Celery-37814A.svg?style=flat-square&logo=Celery&logoColor=white" alt="Celery">
	<br>
	<img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat-square&logo=Python&logoColor=white" alt="Python">
	<img src="https://img.shields.io/badge/Docker-2496ED.svg?style=flat-square&logo=Docker&logoColor=white" alt="Docker">
	<img src="https://img.shields.io/badge/GitHub%20Actions-2088FF.svg?style=flat-square&logo=GitHub-Actions&logoColor=white" alt="GitHub%20Actions">
	<img src="https://img.shields.io/badge/Pytest-0A9EDC.svg?style=flat-square&logo=Pytest&logoColor=white" alt="Pytest">
	<img src="https://img.shields.io/badge/FastAPI-009688.svg?style=flat-square&logo=FastAPI&logoColor=white" alt="FastAPI">
</p>

<br><!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary><br>

- [Overview](#overview)
- [Features](#features)
- [Repository Structure](#repository-structure)
- [Modules](#modules)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Tests](#tests)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [Code of Conduct](#code-of-conduct)
</details>
<hr>

##  Overview

ML-Deploy is a versatile open-source project designed for seamless deployment and scalable management of machine learning models. Leveraging FastAPI, Celery, and Transformers, it offers robust features such as asynchronous task management, context building, and image classification. With Dockerized environments, CI/CD pipelines, and PostgreSQL integration, ML-Deploy ensures efficient ML deployment with enhanced maintainability and scalability. This projects value proposition lies in simplifying ML model deployment processes while enabling reliable and performance-driven AI applications.
[Developper Documentation](https://223mapaction.github.io/ML-Deploy/)

---

## System Arch
The system uses fastApi endpoint to make prediction using the computer vison and the summurization using and LLM

![Selection_071](https://github.com/223MapAction/ML-Deploy/assets/64170643/92f6be3c-7155-4548-9fce-185fd8e54b09)

## How it works

![Selection_067](https://github.com/223MapAction/ML-Deploy/assets/64170643/317e19d8-8b98-4629-93f0-3cbd7326eb77)



---

##  Features

|    |    Feature        | Description                                                                                                                       |
|----|-------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| ⚙️  | **Architecture**  | The project utilizes FastAPI for creating APIs, Celery for asynchronous tasks, and PostgreSQL for database operations.             |
| 🔩 | **Code Quality**  | The codebase maintains high quality with well-structured code, proper error handling, and adherence to PEP8 coding standards.    |
| 📄 | **Documentation** | Extensive documentation includes README, Dockerfile descriptions, and code comments aiding in understanding and maintaining the project. |
| 🔌 | **Integrations**  | Integrates with OpenAI for language model assistance, Redis for Celery task queuing, and GitHub Actions for automated CI/CD processes. |
| 🧩 | **Modularity**    | The codebase is modular with well-defined services for different functionalities like language model processing and image classification. |
| 🧪 | **Testing**       | Testing is done using pytest and pytest-cov for code coverage, ensuring robustness and reliability of the project.                  |
| ⚡️  | **Performance**   | Efficient performance achieved through optimized code, async task processing with Celery, and Docker containers for scalability.   |
| 🛡️ | **Security**      | Implements secure practices including handling sensitive information, maintaining Docker secrets, and CI/CD security measures.   |
| 📦 | **Dependencies**  | Key dependencies include FastAPI, Celery, Transformers, PostgreSQL, and various libraries for image processing and AI model interactions. |

---

##  Repository Structure

```sh
└── ML-Deploy/
    ├── .github
    │   └── workflows
    ├── Dockerfile
    ├── Dockerfile.CI
    ├── Dockerfile.Celery
    ├── LICENSE
    ├── _cd_pipeline.yaml
    ├── _ci_pipeline.yml
    ├── app
    │   ├── __init__.py
    │   ├── apis
    │   ├── database.py
    │   ├── main.py
    │   ├── models
    │   └── services
    ├── requirements.txt
    ├── test
    │   ├── __init__.py
    │   └── apis
    └── vector_index
        └── chroma.sqlite3
```

---

##  Modules

<details closed><summary>.</summary>

| File                                                                                             | Summary                                                                                                                                                                                                                                                                                     |
| ---                                                                                              | ---                                                                                                                                                                                                                                                                                         |
| [requirements.txt](https://github.com/223MapAction/ML-Deploy.git/blob/master/requirements.txt)   | Lists Python package dependencies in requirements.txt for seamless project setup and reproducibility. Key libraries include fastapi, celery, transformers, and uvicorn to support ML deployment. Enhances project scalability and maintainability by managing package versions efficiently. |
| [Dockerfile.Celery](https://github.com/223MapAction/ML-Deploy.git/blob/master/Dockerfile.Celery) | Builds a Docker image for Celery worker, leveraging Python 3.10.13, to manage asynchronous tasks in the ML-Deploy project. Inherits project dependencies from requirements.txt while ensuring a streamlined environment setup for seamless task execution.                                  |
| [Dockerfile](https://github.com/223MapAction/ML-Deploy.git/blob/master/Dockerfile)               | Enables deploying a Python application using Uvicorn server, handling data processing requests. Utilizes Docker for portability, installs dependencies, and configures the execution environment. Dynamically serves the app on port 8001 in the container.                                 |
| [Dockerfile.CI](https://github.com/223MapAction/ML-Deploy.git/blob/master/Dockerfile.CI)         | Builds Python environment, installs project dependencies, and runs test coverage using pytest in the CI pipeline for ML-Deploy.                                                                                                                                                             |
| [_cd_pipeline.yaml](https://github.com/223MapAction/ML-Deploy.git/blob/master/_cd_pipeline.yaml) | Sets up Docker services for a FastAPI app, Redis, and Celery workers with networking configurations in a micro-services environment. Enables communication between services for seamless deployment and scalability.                                                                        |
| [_ci_pipeline.yml](https://github.com/223MapAction/ML-Deploy.git/blob/master/_ci_pipeline.yml)   | Automates creation and configuration of a CI service within the ML-Deploy repository. Orchestrates building a Docker container for testing purposes based on the specified Dockerfile.CI. Integrates environment variables for seamless deployment.                                         |

</details>

<details closed><summary>app</summary>

| File                                                                                     | Summary                                                                                                                                                                                                                                              |
| ---                                                                                      | ---                                                                                                                                                                                                                                                  |
| [main.py](https://github.com/223MapAction/ML-Deploy.git/blob/master/app/main.py)         | Initializes FastAPI app with CORS middleware.-Connects to the database on app startup.-Gracefully disconnects from the database on app shutdown.-Includes main_routers APIs under /api1 prefix.                                                      |
| [database.py](https://github.com/223MapAction/ML-Deploy.git/blob/master/app/database.py) | Establishes a connection to a PostgreSQL database within the ML-Deploy repo's app module. Leveraging the databases library, it initializes a database instance with a predefined URL for subsequent data operations across the ML deployment system. |

</details>

<details closed><summary>app.services.llm</summary>

| File                                                                                                                              | Summary                                                                                                                                                                                                                                                                                                                                             |
| ---                                                                                                                               | ---                                                                                                                                                                                                                                                                                                                                                 |
| [gpt_3_5_turbo.py](https://github.com/223MapAction/ML-Deploy.git/blob/master/app/services/llm/gpt_3_5_turbo.py)                   | Implements a GPT-4 assistant with chat history, user interaction, and error handling. Enables response generation based on user prompts using OpenAIs API. Facilitates chat history display and message exchange within the ML-Deploy repositorys app services architecture.                                                                        |
| [llm.py](https://github.com/223MapAction/ML-Deploy.git/blob/master/app/services/llm/llm.py)                                       | Preprocessing data for improved query results.                                                                                                                                                                                                                                                                                                      |
| [llm_preprocessing.py](https://github.com/223MapAction/ML-Deploy.git/blob/master/app/services/llm/llm_preprocessing.py)           | Generates a chatbot workflow utilizing OpenAI models for conversational retrieval, with document compression and retrieval. Handles document loading, splitting, and vector storage, connecting to a persistent SQLite database. Memory buffer management for conversation history. Summarizes relevant concepts for efficient chatbot interaction. |
| [pgml_llm_preprocessing.py](https://github.com/223MapAction/ML-Deploy.git/blob/master/app/services/llm/pgml_llm_preprocessing.py) | Implements AI chat preprocessing using pgml library with PDF data extraction, semantic search setup, and PostgreSQL integration for ML-Deploy repositorys model training pipeline.                                                                                                                                                                  |
| [pgml_llm.py](https://github.com/223MapAction/ML-Deploy.git/blob/master/app/services/llm/pgml_llm.py)                             | Implements chat bot logic with context building, user input processing, and assistant response generation using AI models and a database connection.                                                                                                                                                                                                |
| [preprocessing.py](https://github.com/223MapAction/ML-Deploy.git/blob/master/app/services/llm/preprocessing.py)                   | Implements a data preprocessing pipeline for a large language model, integrating text splitting, transformation, loading, embeddings, and vector storage. Executes the pipeline with model configurations and a specified tokenizer for NLP tasks within the ML-Deploy repositorys architecture.                                                    |

</details>

<details closed><summary>app.services.celery</summary>

| File                                                                                                               | Summary                                                                                                                                                                                                                                                  |
| ---                                                                                                                | ---                                                                                                                                                                                                                                                      |
| [celery_task.py](https://github.com/223MapAction/ML-Deploy.git/blob/master/app/services/celery/celery_task.py)     | Defines Celery tasks for ML predictions and contextual information retrieval using CNN and LLM models. Handles image predictions and fetches relevant context, impacts, and solutions. Enhances ML-Deploys asynchronous processing capabilities.         |
| [celery_config.py](https://github.com/223MapAction/ML-Deploy.git/blob/master/app/services/celery/celery_config.py) | Defines Celery configuration to enable distributed task processing in the ML-Deploy repositorys architecture. Initializes a Celery object using Redis for task queuing and result storage, enhancing scalability and performance for asynchronous tasks. |

</details>

<details closed><summary>app.services.cnn</summary>

| File                                                                                                              | Summary                                                                                                                                                                                                                                                                                           |
| ---                                                                                                               | ---                                                                                                                                                                                                                                                                                               |
| [cnn_preprocess.py](https://github.com/223MapAction/ML-Deploy.git/blob/master/app/services/cnn/cnn_preprocess.py) | Enables image preprocessing for convolutional neural networks in the ML-Deploy repositorys services module. Implements transformations using the torchvision library to resize, convert, and format images for model input.                                                                       |
| [cnn.py](https://github.com/223MapAction/ML-Deploy.git/blob/master/app/services/cnn/cnn.py)                       | Predicts image classification using a pre-trained VGG16 model for environmental categories. Loads weights from a specified model path, preprocesses input images, and outputs predicted class and probabilities. The CNN model aids in identifying environmental issues like pollution and waste. |
| [cnn_model.py](https://github.com/223MapAction/ML-Deploy.git/blob/master/app/services/cnn/cnn_model.py)           | Refactors VGG16 model for image classification by adjusting classifier layer to predict a specified number of classes. Implements freezing parameters and loading batch normalization weights for enhanced training on ML-Deploy.                                                                 |

</details>

<details closed><summary>app.apis</summary>

| File                                                                                                | Summary                                                                                                                                                                                                                                                                |
| ---                                                                                                 | ---                                                                                                                                                                                                                                                                    |
| [main_router.py](https://github.com/223MapAction/ML-Deploy.git/blob/master/app/apis/main_router.py) | Handles image prediction, contextualization, and data insertion. Utilizes FastAPI, requests, and Celery for async tasks. Fetches images, processes predictions, and stores results in the Mapapi_prediction table. Resilient to exceptions with proper error handling. |

</details>

<details closed><summary>app.models</summary>

| File                                                                                                  | Summary                                                                               |
| ---                                                                                                   | ---                                                                                   |
| [image_model.py](https://github.com/223MapAction/ML-Deploy.git/blob/master/app/models/image_model.py) | Defines ImageModel with image_name, sensitive_structures, and incident_id attributes. |

</details>

<details closed><summary>test.apis</summary>

| File                                                                                                           | Summary                                                                                                                                            |
| ---                                                                                                            | ---                                                                                                                                                |
| [test_main_router.py](https://github.com/223MapAction/ML-Deploy.git/blob/master/test/apis/test_main_router.py) | Verifies FastAPI endpoint functionality by simulating HTTP requests to ensure the Index route returns a 200 status code and correct JSON response. |

</details>

<details closed><summary>.github.workflows</summary>

| File                                                                                                   | Summary                                                                                                                                                                                                               |
| ---                                                                                                    | ---                                                                                                                                                                                                                   |
| [testing.yml](https://github.com/223MapAction/ML-Deploy.git/blob/master/.github/workflows/testing.yml) | Enables automated testing via GitHub Actions by running test suites upon code changes. Ensures continuous integration by validating code quality, fostering robustness and stability within the ML-Deploy repository. |
| [deploy.yml](https://github.com/223MapAction/ML-Deploy.git/blob/master/.github/workflows/deploy.yml)   | Deploys the ML model API via GitHub Actions. Orchestrates docker build and push steps, trigger-based deployment on master branch push events. Secret handling for Docker Hub credentials.                             |

</details>

---

##  Getting Started

**System Requirements:**

* **Python**: `version x.y.z`

###  Installation

<h4>From <code>source</code></h4>

> 1. Clone the ML-Deploy repository:
>
> ```console
> $ git clone https://github.com/223MapAction/ML-Deploy.git
> ```
>
> 2. Change to the project directory:
> ```console
> $ cd ML-Deploy
> ```
>
> 3. Install the dependencies:
> ```console
> $ pip install -r requirements.txt
> ```

###  Usage

<h4>From <code>source</code></h4>

> Run ML-Deploy using the command below:
> ```console
> $ uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
> ```

###  Tests

> Run the test suite using the command below:
> ```console
> $ pytest --cov=app --cov-report term-missing
> ```

---

##  Contributing

Contributions are welcome! Here are several ways you can contribute:

- **[Report Issues](https://github.com/223MapAction/ML-Deploy.git/issues)**: Submit bugs found or log feature requests for the `ML-Deploy` project.
- **[Submit Pull Requests](https://github.com/223MapAction/ML-Deploy.git/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.
- **[Join the Discussions](https://github.com/223MapAction/ML-Deploy.git/discussions)**: Share your insights, provide feedback, or ask questions.

See our [Contribution Guidelines](https://github.com/223MapAction/.github/blob/main/CONTRIBUTING.md) for details on how to contribute.

<details closed>
<summary>Contributor Graph</summary>
<br>
<p align="center">
   <a href="https://github.com{/223MapAction/ML-Deploy.git/}graphs/contributors">
      <img src="https://contrib.rocks/image?repo=223MapAction/ML-Deploy.git">
   </a>
</p>
</details>


---

##  License

This project is protected under the [GNU GPLv3](https://choosealicense.com/licenses/gpl-3.0/) License. For more details, refer to the [LICENSE](https://choosealicense.com/licenses/) file.

---

##  Acknowledgments

- List any resources, contributors, inspiration, etc. here.

[**Return**](#-overview)

---

##  Code of Conduct

See our [Code of Conduct](https://github.com/223MapAction/.github/blob/main/CODE_OF_CONDUCT.md) for details on expected behavior in our community.

---
