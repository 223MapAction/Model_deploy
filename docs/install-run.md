##  Getting Started

**System Requirements:**

* **Python**: `3.x`

###  Installation

<h4>From <code>source</code></h4>

> 1. Clone the ML-Deploy repository:
> ```
> $ git clone https://github.com/223MapAction/ML-Deploy.git
> ```
>
> 2. Change to the project directory:
> ```
> $ cd ML-Deploy
> ```
>
> 3. Create a virtual environement:
> ```
> $ python3 -m venv env
> ```
>
> 4. Install the dependencies:
> ```
> $ pip install -r requirements.txt
> ```

###  Usage

<h4>From <code>source</code></h4>

> Run ML-Deploy using the command below:
> ```
> $ uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
> ```

###  Tests

> Run the test suite using the command below:
> ```console
> $ pytest --cov=app --cov-report term-missing
> ```