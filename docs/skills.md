# Claude Code Skills

Pico-FastAPI includes pre-designed skills for [Claude Code](https://claude.ai/claude-code) that enable AI-assisted development following pico-framework patterns and best practices.

## Available Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Pico FastAPI Endpoint** | `/pico-fastapi` | Creates FastAPI endpoints integrated with pico-ioc |
| **Pico Test Generator** | `/pico-tests` | Generates tests for pico-framework components |

---

## Pico FastAPI Endpoint

Creates endpoints with controller-based routing and dependency injection.

### Controller as Component

```python
from pico_ioc import component
from pico_fastapi import controller, get, post

@controller("/items")
@component
class ItemController:
    def __init__(self, service: ItemService):
        self.service = service

    @get("/")
    async def list_items(self, limit: int = 10):
        return await self.service.list(limit=limit)

    @post("/", status_code=201)
    async def create_item(self, data: ItemCreate):
        return await self.service.create(data)
```

### Router with Injection

```python
from fastapi import APIRouter, Depends
from pico_fastapi import inject

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/")
async def list_items(
    service: ItemService = Depends(inject(ItemService)),
    limit: int = 10,
):
    return await service.list(limit=limit)
```

---

## Pico Test Generator

Generates tests for any pico-framework component.

### Test Structure

```python
import pytest
from fastapi.testclient import TestClient
from pico_ioc import init
from fastapi import FastAPI

class FakeService:
    def greet(self) -> str:
        return "test"

def test_endpoint():
    container = init(
        modules=["controllers", "services", "pico_fastapi"],
        overrides={"MyService": FakeService()}
    )
    app = container.get(FastAPI)
    client = TestClient(app)
    assert client.get("/api/hello").json() == {"msg": "test"}
```

---

## Installation

```bash
# Project-level (recommended)
mkdir -p .claude/skills/pico-fastapi
# Copy the skill YAML+Markdown to .claude/skills/pico-fastapi/SKILL.md

mkdir -p .claude/skills/pico-tests
# Copy the skill YAML+Markdown to .claude/skills/pico-tests/SKILL.md

# Or user-level (available in all projects)
mkdir -p ~/.claude/skills/pico-fastapi
mkdir -p ~/.claude/skills/pico-tests
```

## Usage

```bash
# Invoke directly in Claude Code
/pico-fastapi /api/users
/pico-tests ItemController
```

See the full skill templates in the [pico-framework skill catalog](https://github.com/dperezcabrera/pico-fastapi).
