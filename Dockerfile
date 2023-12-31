FROM python:3.9-slim

WORKDIR /usr/src
ENV PYTHONPATH=/usr/src

# First requirements
RUN pip install poetry
COPY poetry.lock pyproject.toml ./
RUN poetry export --with dev > requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Now code
COPY ./app ./app
COPY ./unit_tests ./unit_tests
COPY ./integration_tests ./integration_tests

CMD python app/main.py
