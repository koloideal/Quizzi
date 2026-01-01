set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]
set shell := ["bash", "-c"]

dev:
    watchfiles --filter python ".venv/Scripts/python -m trudex.application" src

run:
    python -m trudex

lint:
    ruff check src

format:
    isort src
