FROM python:3.11-slim

WORKDIR /usr/src
ENV PYTHONPATH=/usr/src

# Install PostgreSQL client tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Requirements
RUN pip install --no-cache-dir poetry==2.2.1
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && poetry install --no-root

# Now code
COPY ./app ./app
COPY ./tests ./tests
# required for telemetry metrics
COPY service-manifest.json .

EXPOSE 8888

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]
