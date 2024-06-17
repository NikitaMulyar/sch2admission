import datetime

import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    third_name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    class_number = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    status = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    # 0 - В конкурсе, 1 - Выбыл из конкурса, 2 - Принят, 3 - Резерв, 4 - Заявка в обработке
    birth_date = sqlalchemy.Column(sqlalchemy.Date, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    school = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    parent_surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    parent_name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    parent_third_name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    parent_phone_number = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    photo_path = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    profile_10_11 = sqlalchemy.Column(sqlalchemy.String, default='Общий')
    about = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    family_friends_in_l2sh = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    reg_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now())

    invites = orm.relationship("Invite", back_populates="parent_user", cascade="all, delete")

    def __repr__(self):
        return f'<User> {self.id} {self.surname} {self.name}'

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
