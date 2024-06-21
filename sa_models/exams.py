import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Exam(SqlAlchemyBase):
    __tablename__ = 'exams'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    # number = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    date = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)
    exam_description = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    for_class = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    profile_10_11 = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    invites = orm.relationship("Invite", back_populates="parent_exam", cascade="all, delete")

    def __repr__(self):
        return f'<Exam> {self.id} {self.title} {self.date}'

    def as_str(self):
        return f'{self.title}, {self.date.strftime("%H:%M, %d.%m.%Y")}'
