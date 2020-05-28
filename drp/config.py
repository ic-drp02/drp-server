import os

if "DATABASE_URI" in os.environ:
    DATABASE_URI = os.environ.get("DATABASE_URI")
else:
    DATABASE_URI = "postgresql://postgres:drp-dev@localhost:5432/postgres"

IS_DEV_ENV = os.environ.get("FLASK_ENV") == "development"
