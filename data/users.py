from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase
import sqlalchemy as sa
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String, nullable=False)
    about = sa.Column(sa.String, nullable=True)
    email = sa.Column(sa.String, index=True, unique=True, nullable=False)
    hashed_password = sa.Column(sa.String, nullable=False)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)