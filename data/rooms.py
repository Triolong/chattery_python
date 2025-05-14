from .db_session import SqlAlchemyBase
import sqlalchemy as sa


class Room(SqlAlchemyBase):
    __tablename__ = "rooms"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    label = sa.Column(sa.String, nullable=False)
    about = sa.Column(sa.String, nullable=True)

    collaborators = sa.Column(sa.String)