# Setup Instructions

## Table of Contents

1. [Project Setup](#project-setup)
1. [Code Formatting and Quality Tools](#code-formatting-and-quality-tools)
1. [Commit Rules](#commit-rules)
1. [Directory Structure](#directory-structure)
1. [Debugging](#debugging)
1. [Docker](#docker)

## Project Setup

### Setup Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Create Essential Files

```bash
touch .gitignore
touch requirement.txt
touch README.md
```

`.gitignore`
```
#Fast API
__pycache__/
.DS_Store
.Python
build/

*.manifest
*.spec
.vscode

#Environment
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
```

### Install essential dependencies
```bash
pip3 install fastapi uvicorn sqlalchemy python-multipart
```

### Run FastAPI App
```bash
uvicorn main:app --reload
```

## Code Formatting and Quality Tools
### Install Formatter
```bash
pip3 install pylint
pip3 install black
black .
```

## Commit Rules
### Pre Commit Hook
```bash
pip3 install pre-commit
touch .pre-commit-config.yaml
pre-commit install
pre-commit run
```

`.pre-commit-config.yaml`
```
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v2.3.0
    hooks:
    -   id: check-yaml
    -   id: check-json
    -   id: requirements-txt-fixer
    -   id: name-tests-test
-   repo: local
    hooks:
    -   id: pylint
        name: pylint
        entry: pylint
        language: system
        types: [python]
        args:
        - --max-line-length=100
        # - --errors-only
        - --disable=W
-   repo: local
    hooks:
    -   id: black
        name: black
        entry: black
        language: system
        types: [python]

```

## Directory Structure
	.
	├ app1                           # Application 1 (user)
	│  ├── __init__.py
	│  ├── api                       # Holds all apis
	│  │  └── v1                     # API Version 1
	│  │    ├── __init__.py
	│  │    ├── service.py          # Holds all business logic
	│  │    └── app1.py             # Holds the api routes
	│  ├── schemas.py                # pydantic models
	│  ├── models.py                 # db models
	│  ├── config.py                 # local configs
	│  ├── constants.py
	│  └── utils.py
	├ app2                            # Application 2 (blog)
	│  ├── __init__.py
	│  ├── api                       # Holds all apis
	│  │  └── v1                     # API Version 1
	│  │    ├── __init__.py
	│  │    ├── service.py          # Holds all business logic
	│  │    └── app2.py             # Holds the api routes
	│  ├── schemas.py                # pydantic models
	│  ├── models.py                 # db models
	│  ├── config.py                 # local configs
	│  ├── constants.py
	│  └── utils.py
	├ core                   # Holds all global files
	│  ├──  __init__.py
	│  ├── models.py          # Global db models
	│  ├── config.py          # Global configs
	│  ├── database.py        # db connection related stuff
	│  ├── pagination.py      # global module pagination
	│  ├── constants.py       # Global constants
	│  └── utils.py
	├ tests                   # Holds all the test files
	│  ├── app1
	│  ├── app2
	│  └── core
	├── .env                  # Holds all environment variables
	├── docker-compose.yaml
	├── Dockerfile
	├── DB.db                 # Local Database
	├── README.md             # Holds project docs
	├── requirements.txt      # Holds all dependency requirements
	├── .pre-commit-config.yaml  # Holds all dependency requirements
	└── main.py               # Main project file

## Debugging

Inside of your `.vscode` directory create a `launch.json` file:

`launch.json`

```json
{
	"version": "0.2.0",
	"configurations": [
		{
			"name": "Python: FastAPI",
			"type": "python",
			"request": "launch",
			"module": "uvicorn",
			"args": [
				"main:app",
				"--reload"
			],
			"jinja": true,
			"justMyCode": true
		}
	]
}
```

## Docker
### Docker Image
`Dockerfile`

```docker
FROM python:3.11.6-slim

# set the working directory
WORKDIR /app

# install dependencies
COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# copy the all files to docker /app folder
COPY . .

# start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```
Create Docker Image:
```bash
docker build -t fast-api-base .
```

### Start Docker Container

```bash
docker run --name fastapi-base-container -p 8000:8000 -d fastapi-base
```

### Docker Compose Dev Environment
`docker-compose.yml`

```yml
services:
  app:
    build: .
    container_name: fastapi-server
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - 8000:8000
      - 5678:5678
    volumes:
      - .:/app
```

Compose Command:
```
docker-compose up
docker-compose down
```