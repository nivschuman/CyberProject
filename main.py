from flask import Flask
from routes import create_main_blueprint
from db import Database
from secrets import token_urlsafe
from repositories import UserRepository, PostRepository, CommentRepository


def main():
    app = Flask(__name__)
    app.secret_key = token_urlsafe(16)

    @app.after_request
    def set_csp_header(response):
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://cdn.simplecss.org; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp_policy
        return response

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
