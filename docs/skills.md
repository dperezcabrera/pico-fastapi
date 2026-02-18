# AI Coding Skills

[Claude Code](https://code.claude.com) and [OpenAI Codex](https://openai.com/index/introducing-codex/) skills for AI-assisted development with pico-fastapi.

## Installation

```bash
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash -s -- fastapi
```

Or install all pico-framework skills:

```bash
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash
```

### Platform-specific

```bash
# Claude Code only
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash -s -- --claude fastapi

# OpenAI Codex only
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash -s -- --codex fastapi
```

## Available Commands

### `/add-controller`

Creates a FastAPI controller as a pico-ioc component with route decorators. Use when adding REST API endpoints, WebSocket handlers, or HTTP middleware to a pico-fastapi project.

**Generates:** controller class with `@component`, route methods with `@get`/`@post`/`@put`/`@delete`, Pydantic request/response models.

```
/add-controller /api/users
/add-controller /api/orders --websocket
```

### `/add-component`

Creates a new pico-ioc component with dependency injection. Use when adding services, factories, or interceptors.

```
/add-component UserService
```

### `/add-tests`

Generates tests for existing pico-framework components. Creates HTTP tests for controllers and unit tests for services.

```
/add-tests UserController
/add-tests UserService
```

## More Information

See [pico-skills](https://github.com/dperezcabrera/pico-skills) for the full list of skills, selective installation, and details.
