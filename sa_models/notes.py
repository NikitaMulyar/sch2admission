import datetime

import sqlalchemy
from sqlalchemy.orm import relationship

from .db_session import SqlAlchemyBase


class Note(SqlAlchemyBase):
    __tablename__ = 'notes'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    author_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('admins.id'))
    made_on = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    edit_on = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)
    is_important = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    # Просто пометка какая-то будет
    text = sqlalchemy.Column(sqlalchemy.Text, nullable=True)

    author = relationship("Admin", back_populates="notes")

    def __repr__(self):
        return f'<Invite> {self.id} {self.exam_id} {self.user_id}'
