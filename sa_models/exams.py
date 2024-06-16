import sqlalchemy
from .db_session import SqlAlchemyBase
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin


class Exam(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'exams'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    time = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)

    def __repr__(self):
        return f'<Exam> {self.id} {self.title} {self.time}'
