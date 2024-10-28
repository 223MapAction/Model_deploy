## Getting Started

**System Requirements:**

-   **Docker**: Ensure Docker is installed and running on your system.

### Installation

<h4>Using Docker</h4>

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
> 3. Build and start the Docker containers:
>
> ```console
> $ docker-compose -f _cd_pipeline.yaml up --build
> ```

### Usage

<h4>Access the Application</h4>

> Once the containers are up and running, access the application at:
>
> ```console
> http://localhost:8001
> ```

### Tests

> Run the test suite using the command below:
>
> ```console
> $ docker-compose -f _ci_pipeline.yml up
> ```
