import datetime

import sqlalchemy
from sqlalchemy.orm import relationship

from .db_session import SqlAlchemyBase


class Recover(SqlAlchemyBase):
    __tablename__ = 'recovers'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    email = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    code = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    expiration_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                        default=datetime.datetime.now() + datetime.timedelta(hours=1))

    def __repr__(self):
        return f'<Recover> {self.id} {self.email} {self.code}'
