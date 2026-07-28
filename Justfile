set quiet
set dotenv-load

docs-live-browser := "sh -c 'sleep 1; open -a Firefox \\$0' %s &"

@default:
    just --list

# Install dependencies
@install:
    uv sync

# Build Sphinx documentation
@docs:
    uv run sphinx-build -j auto -b html docs docs/_build/html

# Serve documentation with auto-reload (opens Firefox)
@docs-live:
    PYTHON_GIL=1 BROWSER="{{ docs-live-browser }}" uv run sphinx-autobuild docs docs/_build/html --open-browser

# Serve documentation with auto-reload (no browser)
@docs-live-no-open:
    PYTHON_GIL=1 uv run sphinx-autobuild docs docs/_build/html

# Run linting
@lint:
    uv run ruff check .

# Fix linting issues
@lint-fix:
    uv run ruff check --fix .

# Format check
@fmt-check:
    uv run ruff format --check .

# Format the codebase
@fmt:
    uv run ruff format .

# Run tests
@test *ARGS:
    uv run pytest {{ ARGS }}

# Run all quality checks
@quality: lint fmt-check

# Start ds4-server with the current ds4flash.gguf model at 80K context
@serve-ds4:
    cd /Users/pauleveritt/projects/ds4 && ./ds4-server -c 80000 --kv-disk-dir ~/.ds4/server-kv --kv-disk-space-mb 16384

# Clean build artifacts
@clean:
    rm -rf dist/ build/ *.egg-info .pytest_cache .ruff_cache htmlcov/ .coverage
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
