set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]
set shell := ["bash", "-c"]

dev:
    watchfiles --filter python "python -m trudex.application" src

run:
    python -m trudex

lint:
    ruff check src

format:
    isort src
