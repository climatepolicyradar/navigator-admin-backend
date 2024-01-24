FROM python:3.9-slim

WORKDIR /usr/src
ENV PYTHONPATH=/usr/src

# Requires git, easiest
# RUN pip install .  

# First requirements
RUN pip install poetry
COPY poetry.lock pyproject.toml ./

# Current way
RUN poetry config virtualenvs.create false && poetry install --no-cache

# Old way (no working with git library)
# RUN poetry export --with dev > requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# Now code
COPY ./app ./app
COPY ./unit_tests ./unit_tests
COPY ./integration_tests ./integration_tests

CMD python app/main.py
