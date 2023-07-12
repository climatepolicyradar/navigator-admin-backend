FROM python:3.9-slim

WORKDIR /usr/src/app

# First requirements
RUN pip3 install poetry
COPY poetry.lock pyproject.toml ./
RUN poetry export --with dev > requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Now code
COPY ./app .

CMD python3 main.py
