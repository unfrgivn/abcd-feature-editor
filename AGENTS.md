# Agent Guidelines

## Build/Run Commands
- **Frontend dev**: `cd frontend && npm run dev`
- **Frontend build**: `cd frontend && npm run build`
- **Backend run**: `cd backend/app && uv run python main.py` (FastAPI on port 8000)
  - Backend uses `uv` for package management
  - App root is `backend/app` (not `backend`)
  - Virtual env managed by uv in `backend/app/.venv`
- **No test/lint commands configured** - do not assume frameworks

## Code Style

### Python (Backend)
- Use `from module import Class` style imports (see backend/app/main.py)
- Type hints: Use modern syntax `list[str]`, `dict[str, str]` (Python 3.12+)
- Docstrings: Triple-quoted strings for modules and functions
- Config: Use pydantic `BaseSettings` for configuration
- Error handling: Use try/except with logging.error(), return Response with status codes
- Naming: snake_case for functions/variables, PascalCase for classes

### TypeScript/React (Frontend)
- Use React functional components with TypeScript
- Props: Define interfaces with `interface ComponentNameProps`
- Imports: React first, then types, then local services/components
- State: Use `useState<Type>()` with explicit typing
- Naming: camelCase for variables/functions, PascalCase for components/types/interfaces
- Types: Define in separate types.ts file for shared types
