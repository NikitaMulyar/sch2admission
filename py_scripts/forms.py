from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField, BooleanField, StringField, FileField, \
    DateField, TextAreaField, SelectField, TelField, DateTimeLocalField, IntegerField
from wtforms.validators import Optional, InputRequired, ValidationError
from flask_wtf.file import FileAllowed, FileRequired
import phonenumbers

import json
import datetime

from sa_models import db_session
from sa_models.exams import Exam
from sa_models.users import User


def sort_func(user: User):
    user_exams = [user.invites[i].parent_exam.date for i in range(len(user.invites))]
    return max(user_exams) if user_exams else datetime.datetime.now()


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
    email = EmailField('Введите адрес эл. почты', validators=[InputRequired('Обязательное поле')],
                       description='Укажите адрес, указанный при регистрации.')
    password = PasswordField('Введите пароль', validators=[InputRequired('Обязательное поле')],
                             description='Пароль был выслан после регистрации на указанную Вами эл. почту. Проверьте папку "Спам".')
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterFormClasses6To7(FlaskForm):
    email = EmailField('Введите адрес эл. почты', validators=[InputRequired('Обязательное поле')],
                       description='В дальнейшем он будет использоваться для связи, отправления приглашений и входа на сайт. '
                                   'После заполнения формы на него придет пароль от Вашего личного кабинета.')
    surname = StringField('Введите фамилию поступающего', validators=[InputRequired('Обязательное поле')])
    name = StringField('Введите имя поступающего', validators=[InputRequired('Обязательное поле')])
    third_name = StringField('Введите отчество поступающего', validators=[InputRequired('Обязательное поле')])
    class_number = SelectField('Выберите класс, в который ПОСТУПАЕТ ребенок', choices=list(range(6, 8)),
                               validators=[InputRequired('Обязательное поле')], coerce=int,
                               description='Нажмите на поле, чтобы выбрать класс.')
    birth_date = DateField('Введите дату рождения поступающего',
                           validators=[InputRequired('Указана некорректная дата')])
    school = StringField('Введите номер или название школы, в которой сейчас учится поступающий',
                         validators=[InputRequired('Обязательное поле')])
    about = TextAreaField('Напишите об успехах и достижениях ребенка за этот учебный год (олимпиады, конкурсы и др.)',
                          validators=[Optional()], description='Необязательное поле.')
    family_friends_in_l2sh = TextAreaField('Если кто-то из родственников учился или учится в Лицее, Вы можете написать '
                                           'об этом здесь', validators=[Optional()], description='Необязательное поле.')
    parent_surname = StringField('Введите фамилию родителя', validators=[InputRequired('Обязательное поле')])
    parent_name = StringField('Введите имя родителя', validators=[InputRequired('Обязательное поле')])
    parent_third_name = StringField('Введите отчество родителя', validators=[InputRequired('Обязательное поле')])
    parent_phone_number = TelField('Введите номер телефона родителя',
                                   validators=[TelNumberValidator('Неверный формат номера'),
                                               InputRequired()])
    photo = FileField('Прикрепите фото поступающего', validators=[FileRequired('Обязательное поле'),
                                                                  FileAllowed(['png', 'jpg', 'jpeg', 'heic'])])
    submit = SubmitField('Продолжить')


class RegisterFormClasses8To11(RegisterFormClasses6To7):
    class_number = SelectField('Выберите класс, в который ПОСТУПАЕТ ребенок', choices=list(range(8, 12)),
                               validators=[InputRequired('Обязательное поле')], coerce=int,
                               description='Нажмите на поле, чтобы выбрать класс.')
    profile = SelectField('Выберите профиль, в который Вы хотите поступить',
                          choices=json.load(open("py_scripts/consts/profiles.json")),
                          validators=[InputRequired('Обязательное поле')],
                          description='Нажмите на поле, чтобы выбрать профиль.')


class RegisterFormAdmins(FlaskForm):
    email = EmailField('Введите адрес эл. почты', validators=[InputRequired('Обязательное поле')],
                       description='По возможности нужно указать лицейскую почту. После заполнения формы на него '
                                   'придет пароль от Вашего личного кабинета.')
    surname = StringField('Введите Вашу фамилию', validators=[InputRequired('Обязательное поле')])
    name = StringField('Введите Ваше имя', validators=[InputRequired('Обязательное поле')])
    third_name = StringField('Введите Ваше отчество', validators=[InputRequired('Обязательное поле')])
    submit = SubmitField('Продолжить')


class RecoverForm(FlaskForm):
    email = EmailField('Введите адрес эл. почты, на который Вы регистрировались',
                       validators=[InputRequired('Обязательное поле')])
    submit = SubmitField('Получить код')


class ExamCreateForm(FlaskForm):
    title = SelectField('Выберите название экзамена', validators=[InputRequired('Обязательное поле')],
                        description='Нажмите на поле, чтобы выбрать название. Если нет подходящих вариантов, выберите '
                                    '"Другое". В самый первый экзамен эта опция будет выбрана автоматически.',
                        choices=[])
    new_title = StringField('Введите название экзамена')
    date = DateTimeLocalField('Выберите дату и время начала экзамена', validators=[InputRequired('Обязательное поле')])
    class_number = SelectField('Выберите класс', choices=list(range(6, 12)), coerce=int,
                               validators=[InputRequired('Обязательное поле')],
                               description='Нажмите на поле, чтобы выбрать класс.')
    profile = SelectField('Выберите для какого профиля экзамен',
                          choices=json.load(open("py_scripts/consts/profiles.json")),
                          validators=[InputRequired('Обязательное поле')],
                          description='Нажмите на поле, чтобы выбрать профиль.')
    exam_description = TextAreaField('Введите описание экзамена',
                                     description='Для форматирования текста применяйте Markdown: '
                                                 '<a target="_blank" href="https://www.markdownguide.org/basic-syntax/'
                                                 '#emphasis">Пример</a>',
                                     validators=[InputRequired('Обязательное поле')])
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


class InvitesForm:
    def __init__(self):
        pass

    @staticmethod
    def get_part_1():
        class Part1(FlaskForm):
            class_number = SelectField('Выберите класс', choices=list(range(6, 12)),
                                       validators=[InputRequired('Обязательное поле')], coerce=int,
                                       description='Нажмите на поле, чтобы выбрать класс.')
            profile = SelectField('Выберите для какого профиля экзамен',
                                  choices=json.load(open("py_scripts/consts/profiles.json")),
                                  validators=[InputRequired('Обязательное поле')],
                                  description='Нажмите на поле, чтобы выбрать профиль.')
            forward = SubmitField('Далее')
        return Part1()

    @staticmethod
    def get_part_2(**kwargs):
        class Part2(FlaskForm):
            exam = SelectField('Выберите экзамен, на который создаются приглашения', coerce=int, choices=[],
                               validators=[InputRequired('Обязательное поле')],
                               description='Нажмите на поле, чтобы выбрать экзамен.')
            type_of_constructor = SelectField('Выберите тип конструктора',
                                              choices=[(0, 'Полуавтоматический'), (1, 'Ручной')], coerce=int,
                                              validators=[InputRequired('Обязательное поле')],
                                              description='Нажмите на поле, чтобы выбрать тип. В полуавтоматическом '
                                                          'конструкторе вы выбираете макс. число приглашенных человек, '
                                                          'кол-во раз, которое они писали этот экзамен и приоритет, в '
                                                          'котором будут приглашаться поступающие. В ручном '
                                                          'конструкторе вы '
                                                          'самостоятельно выбираете поступающих из списка, заранее '
                                                          'отсортированных по алфавиту. В обоих случаях вы сможете '
                                                          'в конце настройки исключить или добавить людей из '
                                                          'предложенного списка по своему усмотрению.')
            forward = SubmitField('Далее')

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.exam.choices = kwargs['NEW_EXAMS_LIST']
                if not self.validate_on_submit():
                    for ex_id in self.exams_need_ids:
                        ex_ = getattr(self, f'exam_need_{ex_id}')
                        ex_.data = False
                        setattr(self, f'exam_need_{ex_id}', ex_)

        class_n = kwargs['CLASS']
        profile = kwargs['PROFILE']
        db_sess = db_session.create_session()
        new_exams = (db_sess.query(Exam)
                     .filter(Exam.date > datetime.datetime.now(), Exam.for_class == class_n,
                             Exam.profile_10_11 == profile).order_by(Exam.title, Exam.date).all())
        old_exams = (db_sess.query(Exam)
                     .filter(Exam.date <= datetime.datetime.now(), Exam.for_class == class_n,
                             Exam.profile_10_11 == profile).order_by(Exam.title, Exam.date).all())
        new_exams_ = []
        old_exams_ = []
        for ex in new_exams:
            new_exams_.append(
                (ex.id, f"{ex.title} - {ex.date.strftime('%H:%M, %d.%m.%Y')} (ID: {ex.id})")
            )
        for ex in old_exams:
            old_exams_.append(
                (ex.id, f"{ex.title} - {ex.date.strftime('%H:%M, %d.%m.%Y')} (ID: {ex.id})")
            )
        setattr(Part2, 'exams_need_ids', list())
        for ex in old_exams_:
            ex_ = BooleanField(ex[1])
            setattr(Part2, f'exam_need_{ex[0]}', ex_)
            setattr(Part2, 'exams_need_ids', getattr(Part2, 'exams_need_ids') + [ex[0]])
        return Part2(NEW_EXAMS_LIST=new_exams_.copy())

    @staticmethod
    def get_part_a1():
        class PartAuto1(FlaskForm):
            students_number = IntegerField('Введите желаемое число приглашенных людей',
                                           validators=[InputRequired('Обязательное поле')])
            priority = SelectField('Выберите приоритет, в котором будут приглашаться поступающие', coerce=int,
                                   choices=[(0, "По дате регистрации"),
                                            (1, "По дате последнего экзамена")],
                                   validators=[InputRequired('Обязательное поле')],
                                   description='Нажмите на поле, чтобы выбрать вариант.')
            written_0_times = BooleanField('Не писал')
            written_1_times = BooleanField('Писал 1 раз')
            written_2_times = BooleanField('Писал 2 раза')
            forward = SubmitField('Далее')
        return PartAuto1()

    @staticmethod
    def get_part_a2(**kwargs):
        class PartAuto2(FlaskForm):
            forward = SubmitField('Разослать приглашения')

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                if not self.validate_on_submit():
                    for user_id in self.students_ids:
                        ex_ = getattr(self, f'student_{user_id}')
                        ex_.data = True
                        setattr(self, f'student_{user_id}', ex_)

        exam_ids_need = set(kwargs['EXAM_IDS_NEED'])  # list
        limit = kwargs['LIMIT']
        exam_id_new = kwargs['EXAM_ID_NEW']
        times_written = set(kwargs['TIMES_WRITTEN'])  # list
        db_sess = db_session.create_session()
        users = (db_sess.query(User).where(User.status == "0")
                 .filter(User.class_number == kwargs['CLASS'], User.profile_10_11 == kwargs['PROFILE']).all())
        goods = []
        for user in users:
            has_invite_to_new_exam = False
            exam_need = len(exam_ids_need) == 0
            exam_new = False
            count_times_written_exam_new = 0
            for invite in user.invites:
                if invite.parent_exam.id == kwargs['EXAM_ID_NEW']:
                    has_invite_to_new_exam = True
                    break
                if invite.parent_exam.id in exam_ids_need and invite.result == "0":
                    exam_need = True
                if invite.parent_exam.id == exam_id_new:
                    count_times_written_exam_new += 1

            if has_invite_to_new_exam:
                continue
            if count_times_written_exam_new in times_written:
                exam_new = True
            if exam_new and exam_need:
                goods.append(user)
        if kwargs['PRIORITY'] == 0:
            goods = sorted(goods, key=lambda x: x.reg_date)
        else:
            goods = sorted(goods, key=sort_func)
        goods = goods[:limit]
        setattr(PartAuto2, 'students_ids', list())
        for user in goods:
            ex_ = BooleanField(f'{user.surname} {user.name} {user.third_name} ({user.email})')
            setattr(PartAuto2, f'student_{user.id}', ex_)
            setattr(PartAuto2, 'students_ids', getattr(PartAuto2, 'students_ids') + [user.id])
        return PartAuto2()

    @staticmethod
    def get_part_m(**kwargs):
        class PartManual(FlaskForm):
            forward = SubmitField('Разослать приглашения')

            # def __init__(self, *args, **kwargs):
            #     super().__init__(*args, **kwargs)
            #     if not self.validate_on_submit():
            #         for user_id in self.students_ids:
            #             ex_ = getattr(self, f'student_{user_id}')
            #             ex_.data = True
            #             setattr(self, f'student_{user_id}', ex_)

        exam_ids_need = set(kwargs['EXAM_IDS_NEED'])
        db_sess = db_session.create_session()
        users = (db_sess.query(User).where(User.status == "0")
                 .filter(User.class_number == kwargs['CLASS'], User.profile_10_11 == kwargs['PROFILE']).all())
        goods = []
        for user in users:
            has_invite_to_new_exam = False
            exam_need = len(exam_ids_need) == 0
            for invite in user.invites:
                if invite.parent_exam.id == kwargs['EXAM_ID_NEW']:
                    has_invite_to_new_exam = True
                    break
                if invite.parent_exam.id in exam_ids_need and invite.result == "0":
                    exam_need = True

            if has_invite_to_new_exam:
                continue
            if exam_need:
                goods.append(user)
        goods = sorted(goods, key=lambda x: (x.surname, x.name, x.third_name))
        setattr(PartManual, 'students_ids', list())
        for user in goods:
            ex_ = BooleanField(f'{user.surname} {user.name} {user.third_name} ({user.email})')
            setattr(PartManual, f'student_{user.id}', ex_)
            setattr(PartManual, 'students_ids', getattr(PartManual, 'students_ids') + [user.id])
        return PartManual()
