from flask import g, Blueprint, render_template, request, redirect, url_for, session, flash
from repositories import UserRepository, PostRepository, CommentRepository
from db import Database
from models import User, Post, Comment
import bcrypt


def create_main_blueprint(db: Database) -> Blueprint:
    bp = Blueprint('main', __name__)

    def login_required(f):
        from functools import wraps

        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Login required")
                return redirect(url_for("main.login"))
            return f(*args, **kwargs)

        return decorated_function

    def with_repos(f):
        from functools import wraps

        @wraps(f)
        def decorated(*args, **kwargs):
            connection = db.get_connection()
            g.user_repo = UserRepository(connection=connection)
            g.post_repo = PostRepository(connection=connection)
            g.comment_repo = CommentRepository(connection=connection)
            try:
                return f(*args, **kwargs)
            finally:
                connection.close()

        return decorated

    @bp.route("/register", methods=["GET", "POST"])
    @with_repos
    def register():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            if g.user_repo.find_by_username(username):
                flash("Username already taken")
                return redirect(url_for("main.register"))
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            user = User(username=username, password=hashed)
            g.user_repo.save(user)
            flash("Registration successful! Please login.")
            return redirect(url_for("main.login"))
        return render_template("register.html")

    @bp.route("/login", methods=["GET", "POST"])
    @with_repos
    def login():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            user = g.user_repo.find_by_username(username)
            if user and bcrypt.checkpw(password.encode(), user.password):
                session["user_id"] = user.id
                session["username"] = user.username
                flash("Logged in successfully!")
                return redirect(url_for("main.index"))
            flash("Invalid username or password")
        return render_template("login.html")

    @bp.route("/logout")
    @login_required
    def logout():
        session.clear()
        flash("Logged out")
        return redirect(url_for("main.login"))

    @bp.route("/")
    @with_repos
    def index():
        posts = g.post_repo.find_all()
        return render_template("index.html", posts=posts)

    @bp.route("/post/create", methods=["GET", "POST"])
    @login_required
    @with_repos
    def create_post():
        if request.method == "POST":
            title = request.form["title"]
            content = request.form["content"]
            post = Post(user=User(_id=session["user_id"]), title=title, content=content)
            g.post_repo.save(post)
            flash("Post created!")
            return redirect(url_for("main.index"))
        return render_template("create_post.html")

    @bp.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
    @login_required
    @with_repos
    def edit_post(post_id):
        post = g.post_repo.find_by_id(post_id)
        if not post or post.user.id != session["user_id"]:
            flash("Access denied")
            return redirect(url_for("main.index"))

        if request.method == "POST":
            post.title = request.form["title"]
            post.content = request.form["content"]
            g.post_repo.save(post)
            flash("Post updated")
            return redirect(url_for("main.index"))
        return render_template("edit_post.html", post=post)

    @bp.route("/post/<int:post_id>/delete", methods=["POST"])
    @login_required
    @with_repos
    def delete_post(post_id):
        post = g.post_repo.find_by_id(post_id)
        if not post or post.user.id != session["user_id"]:
            flash("Access denied")
        else:
            g.post_repo.delete_by_id(post_id)
            flash("Post deleted")
        return redirect(url_for("main.index"))

    @bp.route("/post/<int:post_id>")
    @with_repos
    def post_detail(post_id):
        post = g.post_repo.find_by_id(post_id)
        if not post:
            flash("Post not found")
            return redirect(url_for("main.index"))

        comments = g.comment_repo.find_by_post_id(post_id)
        return render_template("post_details.html", post=post, comments=comments)

    @bp.route("/comment/create/<int:post_id>", methods=["GET", "POST"])
    @login_required
    @with_repos
    def create_comment(post_id):
        if request.method == "POST":
            content = request.form["content"]
            comment = Comment(post_id=post_id, user=User(_id=session["user_id"]), content=content)
            g.comment_repo.save(comment)
            flash("Comment added")
            return redirect(url_for("main.index"))
        return render_template("create_comment.html", post_id=post_id)

    @bp.route("/comment/<int:comment_id>/edit", methods=["GET", "POST"])
    @login_required
    @with_repos
    def edit_comment(comment_id):
        comment = g.comment_repo.find_by_id(comment_id)
        if not comment or comment.user.id != session["user_id"]:
            flash("Access denied")
            return redirect(url_for("main.index"))
        if request.method == "POST":
            comment.content = request.form["content"]
            g.comment_repo.save(comment)
            flash("Comment updated")
            return redirect(url_for("main.index"))
        return render_template("edit_comment.html", comment=comment)

    @bp.route("/comment/<int:comment_id>/delete", methods=["POST"])
    @login_required
    @with_repos
    def delete_comment(comment_id):
        comment = g.comment_repo.find_by_id(comment_id)
        if not comment or comment.user.id != session["user_id"]:
            flash("Access denied")
        else:
            g.comment_repo.delete_by_id(comment_id)
            flash("Comment deleted")
        return redirect(url_for("main.index"))

    @bp.route("/user/delete", methods=["POST"])
    @login_required
    @with_repos
    def delete_user():
        g.user_repo.delete_by_id(session["user_id"])  # You need delete method in UserRepository
        session.clear()
        flash("User deleted")
        return redirect(url_for("main.register"))

    return bp
