import datetime

from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField, BooleanField, StringField, FileField, \
    DateField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Optional


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterFormClasses6To9(FlaskForm):
    email = EmailField('Введите адрес эл. почты', validators=[DataRequired()],
                       description='В дальнейшем он будет использоваться для связи, отправления приглашений и входа на сайт')
    surname = StringField('Введите фамилию поступающего', validators=[DataRequired()])
    name = StringField('Введите имя поступающего', validators=[DataRequired()])
    third_name = StringField('Введите отчество поступающего', validators=[DataRequired()])
    class_number = SelectField('Выберите класс, в который вы ПОСТУПАЕТЕ', choices=["6", "7", "8", "9"],
                               validators=[DataRequired()],
                               description='Нажмите на поле, чтобы выбрать класс')
    birth_date = DateField('Введите дату рождения поступающего', format='%d.%m.%Y', validators=[DataRequired()],
                           default=datetime.date.today())
    school = StringField('Введите номер или название школы, в которой сейчас учится ребенок',
                         validators=[DataRequired()])
    about = TextAreaField('Напишите о своих успехах и достижениях за этот учебный год (олимпиады, конкурсы и др.)',
                          validators=[Optional()])
    family_friends_in_l2sh = TextAreaField('Если кто-то из родственников учился или учится в Лицее, вы можете написать '
                                           'об этом здесь', validators=[Optional()])
    parent_surname = StringField('Введите фамилию родителя', validators=[DataRequired()])
    parent_name = StringField('Введите имя родителя', validators=[DataRequired()])
    parent_third_name = StringField('Введите отчество родителя', validators=[DataRequired()])
    parent_phone_number = StringField('Введите номер телефона родителя', validators=[DataRequired()])
    photo = FileField('Прикрепите фото поступающего', validators=[DataRequired()])
    submit = SubmitField('Продолжить')


class RegisterFormClasses10To11(RegisterFormClasses6To9):
    profile = SelectField('Выберите профиль, в который вы хотите поступить',
                          choices=["Физический", "Математический", "Математико-программистский",
                                   "Математико-экономический"], validators=[DataRequired()],
                          description='Нажмите на поле, чтобы выбрать профиль')
