FROM python:3.10-slim-buster

WORKDIR /workspace

COPY pyproject.toml pyproject.toml
RUN pip install poetry
RUN poetry install

COPY . .
CMD ["poetry", "run", "python", "launcher.py"]
