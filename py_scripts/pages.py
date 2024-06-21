from flask import render_template, request, make_response, redirect
from flask_login import current_user, login_required
import json
from py_scripts.funcs_back import generate_data_for_base
from sa_models import db_session
from sa_models.exams import Exam
from sa_models.notifications import Notification
from py_scripts.forms import ExamCreateForm

from markupsafe import Markup


class Pages:
    def __init__(self, app):
        app.add_endpoint('/', 'back_index', self.back_index)
        app.add_endpoint('/lk', 'back_cabinet', self.back_cabinet)
        app.add_endpoint('/invites', 'back_invites', self.back_invites)
        app.add_endpoint('/results', 'back_results', self.back_results)
        app.add_endpoint('/contacts', 'back_contacts', self.back_contacts)
        app.add_endpoint('/exams', 'back_exams', self.back_exams)
        app.add_endpoint('/exams/<exam_id>', 'back_exam_info', self.back_exam_info, methods=['GET', 'POST'])

    @staticmethod
    def admin_forbidden(func):
        def wrapper(*args, **kwargs):
            if current_user.is_authenticated and current_user.role == 'admin':
                return redirect('/')
            return func(*args, **kwargs)
        return wrapper

    @staticmethod
    def non_admin_forbidden(func):
        def wrapper(*args, **kwargs):
            if current_user.is_authenticated and current_user.role != 'admin':
                return redirect('/')
            return func(*args, **kwargs)
        return wrapper

    @staticmethod
    def back_index():
        server_data = request.cookies.get("server_data", '')
        resp = make_response(render_template('index.html', **generate_data_for_base(user_id=server_data)))
        resp.set_cookie("server_data", server_data, max_age=0)
        return resp

    @staticmethod
    @login_required
    def back_cabinet():
        statuses = json.load(open('py_scripts/consts/contest_statuses.json', mode='rb'))
        if current_user.role != 'admin':
            data = [
                ("Статус участия", statuses[current_user.status], current_user.status),
                ("Эл. почта", current_user.email),
                ("Поступающий", f"{current_user.surname} {current_user.name} {current_user.third_name}"),
                ("Дата рождения", current_user.birth_date.strftime('%d.%m.%Y')),
                ("Поступает в", f"{current_user.class_number} "
                                f"{current_user.profile_10_11.lower() if current_user.class_number >= 10 else ''} класс"),
                ("Школа", current_user.school),
                ("Родитель", f"{current_user.parent_surname} {current_user.parent_name} {current_user.parent_third_name}"),
                ("Телефон", current_user.parent_phone_number),
                ("О себе", current_user.about if current_user.about else '-')
            ]
        else:
            data = [
                ("Роль", "Администратор сайта", "0"),
                ("Эл. почта", current_user.email),
                ("ФИО", f"{current_user.surname} {current_user.name} {current_user.third_name}"),
            ]
        return render_template('cabinet.html', **generate_data_for_base('/lk', 'Личный кабинет'),
                               data=data)

    @staticmethod
    @admin_forbidden
    @login_required
    def back_invites():
        return render_template('invites.html', **generate_data_for_base('/invites',
                                                                        'Приглашения на вступительные испытания'))

    @staticmethod
    @login_required
    @admin_forbidden
    def back_results():
        return render_template('results.html', **generate_data_for_base('/results',
                                                                        'Результаты вступительных испытаний'))

    @staticmethod
    def back_contacts():
        return render_template('contacts.html', **generate_data_for_base('/contacts',
                                                                         'Контакты'))

    @staticmethod
    @login_required
    @non_admin_forbidden
    def back_exams():
        db_sess = db_session.create_session()
        exams = db_sess.query(Exam).order_by(Exam.date.desc(), Exam.for_class, Exam.profile_10_11, Exam.title).all()
        exams_list = []
        for exam in exams:
            arr = [exam.id, exam.title]
            if exam.for_class >= 10:
                arr.append(f'{exam.for_class} {exam.profile_10_11}')
            else:
                arr.append(exam.for_class)
            arr.append(exam.date.strftime("%H:%M, %d.%m.%Y"))
            exams_list.append(arr)
        return render_template('exams.html', **generate_data_for_base('/exams',
                                                                        'Вступительные испытания'),
                               exams_list=exams_list)

    @staticmethod
    @login_required
    @non_admin_forbidden
    def back_exam_info(exam_id):
        if exam_id == 'create':
            form = ExamCreateForm()

            if form.validate_on_submit():
                profile = ''
                if int(form.class_number.data) >= 10:
                    profile = form.profile.data
                exam = Exam(
                    title=form.title.data,
                    date=form.date.data,
                    exam_description=form.exam_description.data,
                    for_class=int(form.class_number.data),
                    profile_10_11=profile
                )
                notif = Notification(
                    user_id=current_user.id,
                    text=f'Экзамен "{form.title.data}" успешно создан!',
                    type='system'
                )
                notif.set_str_date()
                db_sess = db_session.create_session()
                db_sess.add(exam)
                db_sess.add(notif)
                db_sess.commit()
                db_sess.close()
                return redirect('/exams')
            return render_template('exam_creating.html', **generate_data_for_base('/exams/create',
                                                                          'Создание нового вступительного испытания'),
                                   form=form)
        # МАТВЕЙ, ТУТ ТВОИ ОБРАБОТЧИКИ