# Dockerfile for Prefect Flow on Kubernetes
FROM python:3.11-slim

# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy project configuration
COPY pyproject.toml .

# Install dependencies using uv pip (which installs into system Python by default in containers)
# The '.' installs the current project and its dependencies from pyproject.toml
RUN uv pip install --system .

# Copy the flow code
COPY flow.py .

# The flow will be executed by the Prefect worker
# No need for CMD/ENTRYPOINT - Prefect handles execution
