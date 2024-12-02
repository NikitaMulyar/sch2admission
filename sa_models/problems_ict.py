import datetime

import sqlalchemy
from sqlalchemy.orm import relationship

from .db_session import SqlAlchemyBase


class Problem(SqlAlchemyBase):
    __tablename__ = 'problems'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    kim_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("titles.id"))
    level = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    year = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    # "Текущий учебный год" или конкретный год формата ГГГГ
    author = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    img_file_path = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    text = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    answer = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    title = relationship("Title")

    def __repr__(self):
        return f'<Problem> {self.id} {self.level} {self.text}'
