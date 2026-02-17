# REST API Example

A greeting REST API using pico-fastapi controllers with dependency injection.

## Requirements

- Python 3.11+

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn myapp.main:app --reload
```

## Test

```bash
# Greet someone
curl http://localhost:8000/api/greet/World

# Say goodbye
curl http://localhost:8000/api/greet/World/goodbye
```

## API Docs

Open http://127.0.0.1:8000/docs for interactive Swagger UI.
