import datetime

import sqlalchemy
from sqlalchemy.orm import relationship

from .db_session import SqlAlchemyBase


class Invite(SqlAlchemyBase):
    __tablename__ = 'invites'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    exam_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("exams.id"))
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    made_on = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    edited_on = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)
    result = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    result_description = sqlalchemy.Column(sqlalchemy.Text, nullable=True)

    parent_user = relationship("User", back_populates="invites")
    parent_exam = relationship("Exam", back_populates="invites")

    def __repr__(self):
        return f'<Invite> {self.id} {self.exam_id} {self.user_id}'
