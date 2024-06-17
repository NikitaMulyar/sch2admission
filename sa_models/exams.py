import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Exam(SqlAlchemyBase):
    __tablename__ = 'exams'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    time = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)

    invites = orm.relationship("Invite", back_populates="parent_exam", cascade="all, delete")

    def __repr__(self):
        return f'<Exam> {self.id} {self.title} {self.time}'
