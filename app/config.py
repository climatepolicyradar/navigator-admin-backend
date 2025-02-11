import os

ADMIN_POSTGRES_USER = os.getenv("ADMIN_POSTGRES_USER", "navigator")
ADMIN_POSTGRES_PASSWORD = os.getenv("ADMIN_POSTGRES_PASSWORD", "password")
ADMIN_POSTGRES_HOST = os.getenv("ADMIN_POSTGRES_HOST", "localhost")
ADMIN_POSTGRES_DATABASE = os.getenv("ADMIN_POSTGRES_DATABASE", "navigator")

_creds = f"{ADMIN_POSTGRES_USER}:{ADMIN_POSTGRES_PASSWORD}"
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://{_creds}@{ADMIN_POSTGRES_HOST}:5432/{ADMIN_POSTGRES_DATABASE}"
)

# This used by db-client and alembic script for migrations
os.environ["DATABASE_URL"] = SQLALCHEMY_DATABASE_URI

STATEMENT_TIMEOUT = os.getenv("STATEMENT_TIMEOUT", 10000)  # ms

TOKEN_SECRET_KEY = os.getenv("TOKEN_SECRET_KEY", "")
