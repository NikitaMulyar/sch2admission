from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField, BooleanField, StringField, FileField, \
    DateField, TextAreaField, SelectField, TelField, DateTimeLocalField
from wtforms.validators import DataRequired, Optional, InputRequired, ValidationError
from flask_wtf.file import FileAllowed, FileRequired
import phonenumbers

import json
from markupsafe import Markup

from sa_models import db_session
from sa_models.exams import Exam


class TelNumberValidator:
    def __init__(self, message='Ошибка'):
        self.message = message

    def __call__(self, form, field):
        data = field.data
        try:
            num = phonenumbers.parse(data, 'RU')
            new_num = str(num.country_code) + str(num.national_number)
        except Exception:
            raise ValidationError(self.message)


class LoginForm(FlaskForm):
    email = EmailField('Введите адрес эл. почты', validators=[DataRequired('Обязательное поле')],
                       description='Укажите адрес, указанный при регистрации.')
    password = PasswordField('Введите пароль', validators=[DataRequired('Обязательное поле')],
                             description='Пароль был выслан после регистрации на указанную Вами эл. почту. Проверьте папку "Спам".')
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterFormClasses6To7(FlaskForm):
    email = EmailField('Введите адрес эл. почты', validators=[DataRequired('Обязательное поле')],
                       description='В дальнейшем он будет использоваться для связи, отправления приглашений и входа на сайт. '
                                   'После заполнения формы на него придет пароль от Вашего личного кабинета')
    surname = StringField('Введите фамилию поступающего', validators=[DataRequired('Обязательное поле')])
    name = StringField('Введите имя поступающего', validators=[DataRequired('Обязательное поле')])
    third_name = StringField('Введите отчество поступающего', validators=[DataRequired('Обязательное поле')])
    class_number = SelectField('Выберите класс, в который ПОСТУПАЕТ ребенок', choices=["6", "7"],
                               validators=[DataRequired('Обязательное поле')],
                               description='Нажмите на поле, чтобы выбрать класс')
    birth_date = DateField('Введите дату рождения поступающего',
                           validators=[InputRequired('Указана некорректная дата')])
    school = StringField('Введите номер или название школы, в которой сейчас учится поступающий',
                         validators=[DataRequired('Обязательное поле')])
    about = TextAreaField('Напишите об успехах и достижениях ребенка за этот учебный год (олимпиады, конкурсы и др.)',
                          validators=[Optional()], description='Необязательное поле')
    family_friends_in_l2sh = TextAreaField('Если кто-то из родственников учился или учится в Лицее, Вы можете написать '
                                           'об этом здесь', validators=[Optional()], description='Необязательное поле')
    parent_surname = StringField('Введите фамилию родителя', validators=[DataRequired('Обязательное поле')])
    parent_name = StringField('Введите имя родителя', validators=[DataRequired('Обязательное поле')])
    parent_third_name = StringField('Введите отчество родителя', validators=[DataRequired('Обязательное поле')])
    parent_phone_number = TelField('Введите номер телефона родителя',
                                   validators=[TelNumberValidator('Неверный формат номера'),
                                               DataRequired()])
    photo = FileField('Прикрепите фото поступающего', validators=[FileRequired('Обязательное поле'),
                                                                  FileAllowed(['png', 'jpg', 'jpeg', 'heic'])])
    submit = SubmitField('Продолжить')


class RegisterFormClasses8To11(RegisterFormClasses6To7):
    class_number = SelectField('Выберите класс, в который ПОСТУПАЕТ ребенок', choices=["8", "9", "10", "11"],
                               validators=[DataRequired('Обязательное поле')],
                               description='Нажмите на поле, чтобы выбрать класс')
    profile = SelectField('Выберите профиль, в который Вы хотите поступить',
                          choices=json.load(open("py_scripts/consts/profiles.json")),
                          validators=[DataRequired('Обязательное поле')],
                          description='Нажмите на поле, чтобы выбрать профиль')


class RegisterFormAdmins(FlaskForm):
    email = EmailField('Введите адрес эл. почты', validators=[DataRequired('Обязательное поле')],
                       description='По возможности нужно указать лицейскую почту. После заполнения формы на него придет пароль от Вашего личного кабинета')
    surname = StringField('Введите Вашу фамилию', validators=[DataRequired('Обязательное поле')])
    name = StringField('Введите Ваше имя', validators=[DataRequired('Обязательное поле')])
    third_name = StringField('Введите Ваше отчество', validators=[DataRequired('Обязательное поле')])
    submit = SubmitField('Продолжить')


class RecoverForm(FlaskForm):
    email = EmailField('Введите адрес эл. почты, на который Вы регистрировались',
                       validators=[DataRequired('Обязательное поле')])
    submit = SubmitField('Получить код')


class ExamCreateForm(FlaskForm):
    title = SelectField('Выберите название экзамена', validators=[DataRequired('Обязательное поле')],
                        description='Нажмите на поле, чтобы выбрать название. Если нет подходящих вариантов, выберите '
                                    '"Другое". В самый первый экзамен эта опция будет выбрана автоматически.',
                        choices=[])
    new_title = StringField('Введите название экзамена')
    date = DateTimeLocalField('Выберите дату и время начала экзамена', validators=[DataRequired('Обязательное поле')])
    class_number = SelectField('Выберите класс', choices=["6", "7", "8", "9", "10", "11"],
                               validators=[DataRequired('Обязательное поле')],
                               description='Нажмите на поле, чтобы выбрать класс')
    profile = SelectField('Выберите для какого профиля экзамен',
                          choices=json.load(open("py_scripts/consts/profiles.json")),
                          validators=[DataRequired('Обязательное поле')],
                          description='Нажмите на поле, чтобы выбрать профиль')
    exam_description = TextAreaField('Введите описание экзамена',
                                     description='Для использования форматирования текста применяйте Markdown: '
                                                 '<a target="_blank" href="https://www.markdownguide.org/basic-syntax/'
                                                 '#emphasis">Пример</a>',
                                     validators=[DataRequired('Обязательное поле')])
    submit = SubmitField('Создать экзамен')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        db_sess = db_session.create_session()
        titles = sorted([i[0] for i in db_sess.query(Exam.title.distinct()).all()])
        db_sess.close()
        self.title.choices = titles + ['Другое']


class ExamStatusesForm(FlaskForm):
    exams_6_7 = BooleanField('Статус регистрации на экзамены в 6, 7 классы')
    exams_8_11 = BooleanField('Статус регистрации на экзамены в 8, 9, 10, 11 классы')
    submit = SubmitField('Подтвердить')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.validate_on_submit():
            exs = json.load(open('py_scripts/consts/registration_status.json', mode='rb'))
            self.exams_6_7.data = exs['6-7']
            self.exams_8_11.data = exs['8-11']
