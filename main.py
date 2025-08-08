from flask import Flask
from routes import create_main_blueprint
from db import Database
from repositories import UserRepository, PostRepository, CommentRepository


def main():
    app = Flask(__name__)
    app.secret_key = "secret-key"  # VULNERABILITY: security misconfiguration

    db = Database("databases/app.db")

    connection = db.get_connection()
    UserRepository(connection=connection).initialize()
    PostRepository(connection=connection).initialize()
    CommentRepository(connection=connection).initialize()

    bp = create_main_blueprint(db)
    app.register_blueprint(bp)

    app.run()


if __name__ == '__main__':
    main()
