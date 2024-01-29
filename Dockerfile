FROM python:3.9-slim

WORKDIR /usr/src
ENV PYTHONPATH=/usr/src 

# Requirements
RUN pip install poetry
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && poetry install --no-cache

# Now code
COPY ./app ./app
COPY ./unit_tests ./unit_tests
COPY ./integration_tests ./integration_tests

CMD python app/main.py
