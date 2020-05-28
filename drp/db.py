from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


class Database(SQLAlchemy):
    def __init__(self):
        super().__init__()
        self.migrate = Migrate()

    def init_app(self, app):
        super().init_app(app)
        self.migrate.init_app(app, self)


db = Database()
