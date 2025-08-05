from typing import Optional


class User:
    def __init__(self, _id: Optional[int] = None, username: Optional[str] = None, password: Optional[bytes] = None):
        self.id = _id
        self.username = username
        self.password = password


class Post:
    def __init__(self, _id: Optional[int] = None, user_id: Optional[int] = None, title: Optional[str] = None, content: Optional[str] = None):
        self.id = _id
        self.user_id = user_id
        self.title = title
        self.content = content


class Comment:
    def __init__(self, _id: Optional[int] = None, post_id: Optional[int] = None, user_id: Optional[int] = None, content: Optional[str] = None):
        self.id = _id
        self.post_id = post_id
        self.user_id = user_id
        self.content = content
