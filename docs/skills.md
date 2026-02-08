# Claude Code Skills

[Claude Code](https://code.claude.com) skills for AI-assisted development with pico-fastapi.

## Installation

```bash
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash -s -- fastapi
```

Or install all pico-framework skills:

```bash
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash
```

## Available Commands

| Command | Description |
|---------|-------------|
| `/add-controller` | Add FastAPI controllers with route decorators |
| `/add-component` | Add components, factories, interceptors, settings |
| `/add-tests` | Generate tests for pico-framework components |

## Usage

```
/add-controller /api/users
/add-component UserService
/add-tests UserController
```

## More Information

See [pico-skills](https://github.com/dperezcabrera/pico-skills) for the full list of skills, selective installation, and details.
