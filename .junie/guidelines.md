# Development Guidelines — Openweather MCP Server (FastAPI + MCP over HTTP)

This document captures project-specific knowledge to speed up onboarding and reduce friction during development and debugging.

Audience: advanced developers familiar with Python, FastAPI, pytest, and HTTP/MCP.


## 1) Build and Configuration

### Python and Tooling
- Python: 3.13+ (enforced in `pyproject.toml`).
- Package/build tool: `uv` is recommended for fast, reproducible installs; `pip` works too.
- App framework: FastAPI (`fastapi[full]`).
- Async HTTP client: `httpx`.
- Logging: `loguru` + `rich` (structured console + rotating files).
- JSON: `orjson` (FastAPI response class usage).
- MCP: `fastapi-mcp`, `mcp` and `mcp-proxy`.

### Dependencies
Defined in `pyproject.toml`:
- Runtime deps: `fastapi-mcp`, `fastapi[full]`, `httpx`, `loguru`, `mcp-proxy`, `mcp[cli]`, `orjson`, `python-decouple`, `rich`, `uvicorn`.
- Dev/test deps: `pytest`, `pytest-asyncio`.

Install with uv (preferred):
- Install uv: `pip install uv` (or see uv docs).
- From project root: `uv sync` (creates/updates a lockfile and installs all groups).
  - To include dev group explicitly: `uv sync --group dev`.

Install with pip:
- Editable install for import stability during testing: `pip install -e .[dev]`
  - If your pip doesn’t support PEP 621 extras from `pyproject.toml`, install runtime deps: `pip install fastapi-mcp fastapi[full] httpx loguru mcp-proxy 'mcp[cli]' orjson python-decouple rich uvicorn pytest pytest-asyncio`.

### Environment Configuration
Configuration lives in `utils/config.py` via `python-decouple`. The following variables are consumed at import time (class attributes on `Settings`):
- ACCESS_KEY: OpenWeatherMap API key (required)
- URL: Base URL for external weather API; the app calls `https://api.openweathermap.org/data/2.5/weather` directly in `utils/Weather.py`, but `URL` is required by validation and may be used by clients.
- LOCAL_TOKEN: Bearer token to secure MCP endpoints (required)
- HOST: default `0.0.0.0`
- PORT: default `8000`
- WORKERS: default `1`
- RELOAD: default `False`
- LOG_LEVEL: default `INFO`
- LOG_FILE: default `./logs/mcp_server.log`
- LOG_ROTATION: default `10 MB`
- LOG_RETENTION: default `7 days`
- SESSION_TIMEOUT: default `3600`
- SESSION_CLEANUP_INTERVAL: default `300`

Use a `.env` file at project root during development. Example:
```
ACCESS_KEY=YOUR_OPENWEATHERMAP_KEY
URL=https://api.openweathermap.org/data/2.5
LOCAL_TOKEN=dev-local-token
HOST=127.0.0.1
PORT=8000
RELOAD=true
LOG_LEVEL=DEBUG
LOG_FILE=./logs/mcp_server.log
LOG_ROTATION=10 MB
LOG_RETENTION=7 days
SESSION_TIMEOUT=3600
SESSION_CLEANUP_INTERVAL=300
```
Note: `Settings.validate()` in `utils/config.py` expects `ACCESS_KEY`, `LOCAL_TOKEN`, `URL` to be non-empty.

### Run the Server
- Dev mode with uvicorn reloader:
  - `uv run uvicorn main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --reload`
  - Ensure `.env` is present; `python-decouple` loads it on import.
- Without uv: `python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

### Logging
- Console logging uses `rich` with color, structured format (`utils/logger.py`).
- File logs:
  - Main log: `./logs/mcp_server.log` (rotates, compressed).
  - Error-only log: `./logs/errors.log`.
- Levels are controlled via `LOG_LEVEL`. The logger is set up at module import by calling `setup_logger()` and exporting `log`.


## 2) Testing

This project uses `pytest` with `pytest-asyncio`, `httpx`, and FastAPI’s `TestClient`.

### Quick Start
- Ensure dependencies are installed (see Build and Configuration above).
- Export `PYTHONPATH` to project root so `utils` and `main` are importable during tests when not installed as a package:
  - Bash: `export PYTHONPATH="$(pwd)"`
  - One-off: `PYTHONPATH=. pytest -q`
- Alternatively, install in editable mode: `pip install -e .[dev]` then just `pytest -q`.

### Running the Suite
- Full suite: `pytest -q`
- Filtered by filename: `pytest -q tests/test_main.py`
- Filtered by keyword: `pytest -q -k mcp_initialize`
- Show logs: `pytest -q -s` (or use `--log-cli-level=INFO` to show std logs; note Loguru’s rich console output is handled separately).

### Async Tests
- Many tests are `@pytest.mark.asyncio`. Ensure `pytest-asyncio` is installed (dev group). The event loop policy defaults are fine for CPython.

### HTTP/MCP Isolation and Mocking
- External HTTP calls should be isolated:
  - `utils/Weather.weather_request` uses `httpx.get`. Tests patch the higher-level `main.weather_request` entry point (see `tests/test_main.py`) to avoid real network requests.
- Authentication during MCP tests:
  - `utils.auth.LocalTokenValidator.validate_token` is patched in tests to bypass real token checks.
- Examples from the suite:
  - `@patch("main.weather_request")` to stub weather fetches.
  - `@patch("utils.auth.LocalTokenValidator.validate_token")` to force auth outcome.

### Environment for Tests
- Tests do not require a live server; they instantiate FastAPI app and use `TestClient`.
- `.env` variables may be loaded at import time by `utils/config`. For hermetic tests, either:
  - Provide minimal `.env` (ACCESS_KEY, LOCAL_TOKEN, URL), or
  - Patch `utils.config.settings` attributes inside tests, or
  - Set environment variables before running pytest.

### Creating and Running a Minimal Test (Demonstration)
- To demonstrate `pytest` works independently of project modules, we executed a temporary smoke test file:
  - Created `tests/test_smoke_demo.py` with a trivial assertion.
  - Ran: `PYTHONPATH=. pytest -q tests/test_smoke_demo.py` → 1 passed.
  - Removed the temporary file after the run, per instructions.
- This validates your test runner installation. To run the project’s tests, ensure all runtime deps are installed (including `loguru`, `rich`, `fastapi`, `httpx`, etc.) and `PYTHONPATH` is set or the project is installed in editable mode.

### Adding New Tests
- Place tests under `tests/` with descriptive names.
- Prefer testing via the public surface:
  - REST endpoints: use `TestClient(app)`.
  - MCP: exercise JSON-RPC endpoints via FastAPI routes; patch auth and tool calls.
- Mock at module boundaries:
  - Network: patch `main.weather_request` or `httpx.get` within `utils/Weather.py` depending on granularity.
  - Auth: patch `utils.auth.LocalTokenValidator.validate_token`.
- Example skeleton for an async endpoint unit test:
```
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

@pytest.mark.asyncio
@patch("main.weather_request")
async def test_weather_ok(mock_weather_request):
    mock_weather_request.return_value = ... # a real Weather dataclass or dict compatible
    client = TestClient(app)
    resp = client.get("/weather/London/GB")
    assert resp.status_code == 200
```


## 3) Additional Development Information

### Project Structure Highlights
- `main.py`: FastAPI app, REST + MCP endpoints, integrates logging and auth.
- `utils/Weather.py`: `Weather` dataclass + `weather_request` function (`httpx.get` to OpenWeatherMap, raises `HTTPException` on errors/timeouts).
- `utils/auth.py`: Bearer validation for MCP endpoints (`LocalTokenValidator`). Tests patch it.
- `utils/config.py`: Centralized settings loaded with `python-decouple` and validated via `Settings.validate()`.
- `utils/logger.py`: Opinionated logging setup with rich console, file rotation, and a JSON/pretty helper API.
- `weather_mcp_client.py`: Minimal MCP client to exercise the MCP endpoints.
- `tests/`: Comprehensive suite covering REST and MCP flows; relies on patching to avoid I/O.

### Code Style and Conventions
- Typing: use explicit type hints throughout; prefer `dataclass` for value objects (see `Weather`).
- HTTP errors: raise `fastapi.HTTPException` with appropriate `status` constants; tests are explicit about 404/503/408 semantics.
- Logging: use `log` from `utils/logger.py`. For JSON-like payloads, leverage the log helpers (`log_json`, etc.) if present.
- Responses: prefer `ORJSONResponse` for performance when returning JSON payloads.
- Configuration: don’t import settings deeply in leaf modules unless necessary. For new modules, centralize all settings access in a thin configuration layer to keep import-time effects predictable.

### Common Pitfalls and Remedies
- Module import errors in tests (`ModuleNotFoundError: utils`):
  - Use `PYTHONPATH=.` or `pip install -e .[dev]`.
- Missing runtime deps in CI/dev env leading to import errors (e.g., `loguru`, `rich`, `httpx`):
  - Run `uv sync --group dev` or `pip install -e .[dev]` before tests.
- `.env` not present → `Settings.validate()` may fail or logging paths may default unexpectedly:
  - Provide a minimal `.env` during local runs, or patch settings in tests.
- External HTTP requests during tests (long or flaky):
  - Patch `main.weather_request` or `httpx.get` and return canned payloads.

### Running the MCP Client (Local)
- With server running on `http://127.0.0.1:8000` and `LOCAL_TOKEN` configured:
  - `python weather_mcp_client.py --base-url http://127.0.0.1:8000 --token "$LOCAL_TOKEN"`
- You can also use `mcp` CLI or MCP Inspector to introspect the service.

### Logging and Observability Tips
- For local debugging, set `LOG_LEVEL=DEBUG` and `RELOAD=true` in `.env`.
- Logs persist under `./logs/`. Check `errors.log` for stack traces; files are rotated and compressed automatically.

### Versioning and Reproducibility
- Prefer `uv` for lockfile-driven reproducibility. Commit `uv.lock` whenever dependencies change.


## 4) Verified Test Demonstration (Executed Now)
- Created a temporary test `tests/test_smoke_demo.py` with one assertion.
- Ran: `PYTHONPATH=. pytest -q tests/test_smoke_demo.py` → 1 test passed.
- Deleted the temporary file to keep the repository clean, as required.

To run the project’s full test suite successfully in your environment, ensure all runtime and dev dependencies are installed and that imports resolve (either via `PYTHONPATH=.` or editable install).
