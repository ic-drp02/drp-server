import os

if "DATABASE_URI" in os.environ:
    DATABASE_URI = os.environ.get("DATABASE_URI")
else:
    DATABASE_URI = "postgresql://postgres:drp-dev@localhost:5432/postgres"

IS_DEV_ENV = os.environ.get("FLASK_ENV") == "development"

JWT_ISSUER = "drp02"
JWT_AUDIENCE = "drp02"

if IS_DEV_ENV:
    JWT_SECRET_KEY = "bhO.#v8En8ka8O|ZX*59B`kD3V7ZF7#V^u67TkMCV50.:H7awQ3MTGHJIJd>H<N"  # noqa: E501
else:
    JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
