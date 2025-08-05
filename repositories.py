from sqlite3 import Connection
from models import User, Post, Comment
from typing import Optional, List


class UserRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    def initialize(self):
        cursor = self.connection.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL
        )
        """)
        self.connection.commit()

    def save(self, user: User) -> User:
        cursor = self.connection.cursor()
        if user.id is None:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (user.username, user.password)
            )
            user.id = cursor.lastrowid
        else:
            cursor.execute(
                "UPDATE users SET username = ?, password = ? WHERE id = ?",
                (user.username, user.password, user.id)
            )
        self.connection.commit()
        return user

    def find_by_username(self, username: str) -> Optional[User]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        row = cursor.fetchone()
        if row:
            return User(_id=row["id"], username=row["username"], password=row["password"])
        return None

    def delete_by_id(self, user_id: int) -> bool:
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.connection.commit()
        return cursor.rowcount > 0


class PostRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    def initialize(self):
        cursor = self.connection.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        self.connection.commit()

    def save(self, post: Post) -> Post:
        cursor = self.connection.cursor()
        if post.id is None:
            cursor.execute(
                "INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)",
                (post.user.id, post.title, post.content)
            )
            post.id = cursor.lastrowid
        else:
            cursor.execute(
                "UPDATE posts SET title = ?, content = ? WHERE id = ?",
                (post.title, post.content, post.id)
            )
        self.connection.commit()
        return post

    def find_by_id(self, _id: int) -> Optional[Post]:
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT p.id as post_id, p.title, p.content, 
                   u.id as user_id, u.username, u.password
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.id = ?
        """, (_id,))
        row = cursor.fetchone()
        if row:
            user = User(_id=row["user_id"], username=row["username"], password=row["password"])
            return Post(_id=row["post_id"], user=user, title=row["title"], content=row["content"])
        return None

    def find_all(self) -> List[Post]:
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT p.id as post_id, p.title, p.content,
                   u.id as user_id, u.username, u.password
            FROM posts p
            JOIN users u ON p.user_id = u.id
        """)
        rows = cursor.fetchall()
        return [
            Post(
                _id=row["post_id"],
                user=User(_id=row["user_id"], username=row["username"], password=row["password"]),
                title=row["title"],
                content=row["content"]
            )
            for row in rows
        ]

    def delete_by_id(self, _id: int) -> bool:
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM posts WHERE id = ?", (_id,))
        self.connection.commit()
        return cursor.rowcount > 0


class CommentRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    def initialize(self):
        cursor = self.connection.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY(post_id) REFERENCES posts(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        self.connection.commit()

    def save(self, comment: Comment) -> Comment:
        cursor = self.connection.cursor()
        if comment.id is None:
            cursor.execute(
                "INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
                (comment.post_id, comment.user.id, comment.content)
            )
            comment.id = cursor.lastrowid
        else:
            cursor.execute(
                "UPDATE comments SET content = ? WHERE id = ?",
                (comment.content, comment.id)
            )
        self.connection.commit()
        return comment

    def find_by_id(self, comment_id: int) -> Optional[Comment]:
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT c.id as comment_id, c.post_id, c.content,
                   u.id as user_id, u.username, u.password
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.id = ?
        """, (comment_id,))
        row = cursor.fetchone()
        if row:
            user = User(_id=row["user_id"], username=row["username"], password=row["password"])
            return Comment(
                _id=row["comment_id"],
                post_id=row["post_id"],
                user=user,
                content=row["content"]
            )
        return None

    def delete_by_id(self, comment_id: int) -> bool:
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        self.connection.commit()
        return cursor.rowcount > 0

    def find_by_post_id(self, post_id: int) -> List[Comment]:
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT c.id as comment_id, c.post_id, c.content,
                   u.id as user_id, u.username, u.password
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ?
        """, (post_id,))
        rows = cursor.fetchall()
        return [
            Comment(
                _id=row["comment_id"],
                post_id=row["post_id"],
                user=User(_id=row["user_id"], username=row["username"], password=row["password"]),
                content=row["content"]
            )
            for row in rows
        ]
