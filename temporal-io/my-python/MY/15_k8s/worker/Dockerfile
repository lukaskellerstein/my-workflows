# Dockerfile for Temporal Worker
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml /app/
COPY worker.py /app/

# Install dependencies using uv
RUN uv pip install --system -r pyproject.toml

# Create non-root user for security
RUN useradd -m -u 1000 temporal && \
    chown -R temporal:temporal /app

USER temporal

# Run the worker
CMD ["python", "worker.py"]
