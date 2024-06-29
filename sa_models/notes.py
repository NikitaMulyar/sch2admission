import datetime

import sqlalchemy
from sqlalchemy.orm import relationship

from .db_session import SqlAlchemyBase


class Note(SqlAlchemyBase):
    __tablename__ = 'notes'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    author_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    made_on = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    edit_on = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    path_show_config = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    text = sqlalchemy.Column(sqlalchemy.Text, nullable=True)

    author = relationship("User", back_populates="notes")

    def __repr__(self):
        return f'<Note> {self.id} {self.author_id} {self.text}'
