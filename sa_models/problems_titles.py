import datetime

import sqlalchemy
from sqlalchemy.orm import relationship

from .db_session import SqlAlchemyBase


class Title(SqlAlchemyBase):
    __tablename__ = 'titles'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    number = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    points = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)

    def __repr__(self):
        return f'<Title> {self.id} {self.number} {self.title}'
