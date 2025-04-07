# ---- Build stage ----
FROM python:3.12-slim AS builder

# System deps
RUN apt-get update && apt-get install -y curl git build-essential

# Install poetry
ENV POETRY_VERSION=1.8.2 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Set workdir
WORKDIR /app

# Copy pyproject & lock first (for caching)
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --only main

# Copy full code
COPY . .

# Optional: confirm install
RUN python -c "import rtdata; print('✅ rtdata installed')"

# ---- Runtime stage ----
FROM python:3.12-slim

WORKDIR /app

# Copy from builder
COPY --from=builder /app /app

# Set command to run your script
CMD ["python", "plotting/Gearth.py"]
