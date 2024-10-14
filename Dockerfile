FROM python:3.10-slim

WORKDIR /usr/src
ENV PYTHONPATH=/usr/src

# Requirements
RUN pip install --no-cache-dir poetry==1.7.1
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && poetry install --no-directory --no-root

# Now code
COPY ./app ./app
COPY ./tests ./tests

CMD python app/main.py
