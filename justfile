set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]
set shell := ["bash", "-c"]

dev:
    watchfiles --filter python ".venv/Scripts/python -m quizzi.application" src

run:
    python -m quizzi.application

lint:
    ruff check src

format:
    isort src
