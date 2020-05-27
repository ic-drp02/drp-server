from flask import Flask, escape, request

app = Flask(__name__)


@app.route("/")
def hello():
    name = request.args.get("name", "World")
    return f"Hello, {escape(name)}!"

# Example database code
#
# from sqlalchemy import create_engine
#
# db = create_engine(
#     "postgresql://postgres:drp-dev@localhost:5432/postgres")

# db.execute("CREATE TABLE IF NOT EXISTS users (name TEXT, email TEXT)")
# db.execute("INSERT INTO users (name, email) VALUES ('Bob', 'bob@gmail.com')")

# results = db.execute("SELECT * FROM users")
# for row in results:
#     print(row)
