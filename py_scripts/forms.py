from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField, BooleanField, StringField, FileField, \
    DateField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Optional, InputRequired
from flask_wtf.file import FileAllowed, FileRequired


class LoginForm(FlaskForm):
    email = EmailField('Введите адрес эл. почты', validators=[DataRequired()],
                       description='Укажите адрес, указанный при регистрации.')
    password = PasswordField('Введите пароль', validators=[DataRequired()],
                             description='Пароль был выслан после регистрации на указанную вами эл. почту. Проверьте папку "Спам".')
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterFormClasses6To9(FlaskForm):
    email = EmailField('Введите адрес эл. почты', validators=[DataRequired()],
                       description='В дальнейшем он будет использоваться для связи, отправления приглашений и входа на сайт. '
                                   'После заполнения формы на него придет пароль от вашего личного кабинета')
    surname = StringField('Введите фамилию поступающего', validators=[DataRequired()])
    name = StringField('Введите имя поступающего', validators=[DataRequired()])
    third_name = StringField('Введите отчество поступающего', validators=[DataRequired()])
    class_number = SelectField('Выберите класс, в который ПОСТУПАЕТ ребенок', choices=["6", "7", "8", "9"],
                               validators=[DataRequired()],
                               description='Нажмите на поле, чтобы выбрать класс')
    birth_date = DateField('Введите дату рождения поступающего', validators=[InputRequired()])
    school = StringField('Введите номер или название школы, в которой сейчас учится ребенок',
                         validators=[DataRequired()])
    about = TextAreaField('Напишите о своих успехах и достижениях за этот учебный год (олимпиады, конкурсы и др.)',
                          validators=[Optional()], description='Необязательное поле')
    family_friends_in_l2sh = TextAreaField('Если кто-то из родственников учился или учится в Лицее, вы можете написать '
                                           'об этом здесь', validators=[Optional()], description='Необязательное поле')
    parent_surname = StringField('Введите фамилию родителя', validators=[DataRequired()])
    parent_name = StringField('Введите имя родителя', validators=[DataRequired()])
    parent_third_name = StringField('Введите отчество родителя', validators=[DataRequired()])
    parent_phone_number = StringField('Введите номер телефона родителя', validators=[DataRequired()])
    photo = FileField('Прикрепите фото поступающего', validators=[FileRequired(),
                                                                  FileAllowed(['png', 'jpg', 'jpeg', 'heic'])])
    submit = SubmitField('Продолжить')


class RegisterFormClasses10To11(RegisterFormClasses6To9):
    class_number = SelectField('Выберите класс, в который вы ПОСТУПАЕТЕ', choices=["10", "11"],
                               validators=[DataRequired()],
                               description='Нажмите на поле, чтобы выбрать класс')
    profile = SelectField('Выберите профиль, в который вы хотите поступить',
                          choices=["Физический", "Математический", "Математико-программистский",
                                   "Математико-экономический"], validators=[DataRequired()],
                          description='Нажмите на поле, чтобы выбрать профиль')


class RegisterFormAdmins:
    email = EmailField('Введите адрес эл. почты', validators=[DataRequired()],
                       description='По возможности нужно указать лицейскую почту. После заполнения формы на него придет пароль от вашего личного кабинета')
    surname = StringField('Введите вашу фамилию', validators=[DataRequired()])
    name = StringField('Введите ваше имя', validators=[DataRequired()])
    third_name = StringField('Введите ваше отчество', validators=[DataRequired()])
