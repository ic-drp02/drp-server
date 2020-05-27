from flask import Flask, escape, request
from flask_sqlalchemy import SQLAlchemy

from . import config

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URI
app.config["SQLALCHEMY_ECHO"] = config.IS_DEV_ENV
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


@app.route("/")
def hello():
    name = request.args.get("name", "World")
    return f"Hello, {escape(name)}!"

# Example database code
#
# from flask import jsonify
#
# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80), unique=True, nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)

#     def __repr__(self):
#         return f"<User {self.username}>"
#
#
# @app.route("/users/")
# def get_users():
#     users = [{'username': user.username, 'email': user.email}
#              for user in User.query.all()]
#     return jsonify(users)
