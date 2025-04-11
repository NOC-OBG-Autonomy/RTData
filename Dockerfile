FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y curl build-essential git

# Install Poetry
ENV POETRY_VERSION=1.8.2 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Set working directory
WORKDIR /app

# Copy pyproject and lock
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --only main

# Copy rest of code
COPY . .

# Set PYTHONPATH to find local packages
ENV PYTHONPATH=/app

#Scripts to run
CMD ["python", "plotting/Gearth.py"]


#Build the container 
#docker build --no-cache -t automatic_position .
#Run the container
#docker run --rm -v ${PWD}:/app automatic_position
