import datetime

import sqlalchemy
from sqlalchemy.orm import relationship

from .db_session import SqlAlchemyBase


class Notification(SqlAlchemyBase):
    __tablename__ = 'notifications'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    made_on = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    made_on_str = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    type = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    text = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    link = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    parent_user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f'<Notif> {self.id} {self.user_id} {self.text}'

    def set_str_date(self):
        if self.made_on is None:
            self.made_on = datetime.datetime.now()
        self.made_on_str = self.made_on.strftime('%H:%M, %d.%m.%Y')
