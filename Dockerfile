FROM python:3.9-slim

WORKDIR /usr/src
ENV PYTHONPATH=/usr/src

# Requirements
RUN pip install --no-cache-dir poetry==1.6.1
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && poetry install

# Now code
COPY ./app ./app
COPY ./unit_tests ./unit_tests
COPY ./integration_tests ./integration_tests

CMD python app/main.py
