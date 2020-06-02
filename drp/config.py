import os

if "DATABASE_URI" in os.environ:
    DATABASE_URI = os.environ.get("DATABASE_URI")
else:
    DATABASE_URI = "postgresql://postgres:drp-dev@localhost:5432/postgres"

IS_DEV_ENV = os.environ.get("FLASK_ENV") == "development"

if "UPLOAD_FOLDER" in os.environ:
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER")
else:
    root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    UPLOAD_FOLDER = os.path.join(root, "uploads")


ALLOWED_FILE_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg',
                           'jpeg', 'gif', 'doc', 'docx',
                           'xls', 'xlsx', 'ppt', 'pptx',
                           'ods', 'fods', 'ods', 'fods',
                           'odp', 'fodp', 'md'}
