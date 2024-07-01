import datetime

from flask import render_template, request, make_response, redirect, jsonify
from flask_login import current_user, login_required
import json
from py_scripts.funcs_back import generate_data_for_base
from sa_models import db_session
from sa_models.exams import Exam
from sa_models.notifications import Notification
from py_scripts.forms import ExamCreateForm
from sa_models.users import User
from sa_models.invites import Invite
from sqlalchemy import desc, and_

from markupsafe import Markup


class Pages:
    def __init__(self, app):
        app.add_endpoint('/', 'back_index', self.back_index)
        app.add_endpoint('/lk', 'back_cabinet', self.back_cabinet)
        app.add_endpoint('/invites', 'back_invites', self.back_invites)
        app.add_endpoint('/results', 'back_results', self.back_results)
        app.add_endpoint('/contacts', 'back_contacts', self.back_contacts)
        app.add_endpoint('/exams', 'back_exams', self.back_exams)
        app.add_endpoint('/participants', 'table_of_users', self.table_of_users, methods=['GET', 'POST'])
        app.add_endpoint('/exams/<exam_id>', 'back_exam_info', self.back_exam_info, methods=['GET', 'POST'])
        app.add_endpoint('/users/<user_id>', 'user_info_for_admin', self.user_info_for_admin, methods=['GET', 'POST'])
        app.add_endpoint('/update', 'update_result', self.update_result, methods=["POST"])

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
                ("Родитель",
                 f"{current_user.parent_surname} {current_user.parent_name} {current_user.parent_third_name}"),
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
        else:
            if request.method == "POST":
                select = request.form.get('result_select')
                db_sess = db_session.create_session()
                invite = db_sess.query(Invite).filter(
                    and_(Invite.exam_id == exam_id, Invite.user_id == int(select.split("_")[1]))).first()
                invite.result = select.split("_")[0]
                invite.edited_on = datetime.datetime.now()
                db_sess.commit()
                db_sess.close()
            db_sess = db_session.create_session()
            kwargs = dict()
            kwargs["exam_id"] = exam_id
            exam = db_sess.query(Exam).filter(Exam.id == exam_id).first()
            exam_description = exam.exam_description if exam.exam_description else "Не указано"
            kwargs["exam_info"] = {"ID": exam.id, "Название": exam.title, "Дата": exam.date,
                                   "Описание экзамена": exam_description}
            if exam.for_class < 10:
                kwargs["exam_info"]["Класс"] = exam.for_class
            else:
                f"{exam.for_class}, {exam.profile_10_11}"

            participants = db_sess.query(Invite).filter(Invite.exam_id == exam_id).all()
            kwargs["users"] = list()
            kwargs["res_opt"] = json.load(open('py_scripts/consts/results.json', mode='rb'))
            for el in participants:
                result = kwargs["res_opt"][el.result] if el.result else "Результат не установлен"
                result_description = el.result_description if el.result_description else "Не указано"
                kwargs["users"].append(
                    {"ID": el.user_id,
                     "ФИО": f"{el.parent_user.surname} {el.parent_user.name} {el.parent_user.third_name}",
                     "Почта": el.parent_user.email, "Результат": result, "Описание результата": result_description})
            return render_template("exam_table.html",
                                   **generate_data_for_base('/exams/<exam_id>', 'Информация об экзамене'), **kwargs)

    @staticmethod
    @login_required
    @non_admin_forbidden
    def table_of_users():
        kwargs = dict()
        kwargs["checked_grades"] = [i for i in range(6, 12)]
        if request.method == "POST" and request.form.getlist('grade'):
            kwargs["checked_grades"] = [int(el) for el in request.form.getlist('grade')]
        statuses = json.load(open('py_scripts/consts/contest_statuses.json', mode='rb'))
        db_sess = db_session.create_session()

        # import datetime
        # inv1 = Invite(user_id=2, exam_id=1, made_on=datetime.datetime(year=2024, day=29, month=6))
        # db_sess.add(inv1)
        # inv1 = Invite(user_id=2, exam_id=1, made_on=datetime.datetime(year=2024, day=30, month=6))
        # db_sess.add(inv1)
        # db_sess.commit()

        kwargs["users"] = []
        users = db_sess.query(User).all()
        # kwargs["options_1"] = {i + 1: el for i, el in enumerate(statuses)}
        kwargs["options_2"] = {i + 1: el for i, el in enumerate(range(6, 12))}
        kwargs["grades"] = [i for i in range(6, 12)]
        for el in users:
            if el.role != "admin" and el.class_number in kwargs["checked_grades"]:
                for_modal = [("ФИО", f"{el.surname} {el.name} {el.third_name}"), ("Эл. почта", el.email)]
                if el.class_number >= 10:
                    for_modal.append(("Класс поступления", f"{el.class_number}, {el.profile_10_11} профиль"))
                else:
                    for_modal.append(("Класс поступления", el.class_number))
                for_modal.extend(
                    [("Дата рождения", el.birth_date), ("Статус участия", statuses[el.status]), ("Школа", el.school),
                     ("Контакты родителя",
                      f"{el.parent_surname} {el.parent_name} {el.parent_third_name}, {el.parent_phone_number}")])

                exams = db_sess.query(Invite).filter(Invite.user_id == el.id).order_by(desc(Invite.made_on)).all()
                for_exam = []
                for exam in exams:
                    exam_description = exam.parent_exam.exam_description if exam.parent_exam.exam_description else "Не указано"
                    result = exam.result if exam.result else "Результат не установлен"
                    result_description = exam.result_description if exam.result_description else "Не указано"
                    for_exam.append({"ID": str(exam.exam_id), "Название экзамена": exam.parent_exam.title,
                                     "Дата": exam.parent_exam.date.strftime("%d/%m/%Y %H:%M:%S"),
                                     "Описание экзамена": exam_description,
                                     "Результат": result,
                                     "Описание результата": result_description})
                kwargs["users"].append([f"{el.surname} {el.name} {el.third_name}", el.email, el.class_number,
                                        statuses[el.status], for_modal, for_exam, el.id])

        return render_template('table_of_users.html',
                               **generate_data_for_base("/participants", title="Список поступающих"), **kwargs)

    @staticmethod
    @login_required
    @non_admin_forbidden
    def user_info_for_admin(user_id):
        if request.method == "POST":
            select = request.form.get('result_select')
            db_sess = db_session.create_session()
            invite = db_sess.query(Invite).filter(
                and_(Invite.exam_id == int(select.split("_")[1]), Invite.user_id == user_id)).first()
            invite.result = select.split("_")[0]
            invite.edited_on = datetime.datetime.now()
            db_sess.commit()
            db_sess.close()
        kwargs = dict()
        statuses = json.load(open('py_scripts/consts/contest_statuses.json', mode='rb'))
        db_sess = db_session.create_session()

        kwargs["user_info"] = []
        user = db_sess.query(User).filter(User.id == user_id).first()
        for_modal = [("ФИО", f"{user.surname} {user.name} {user.third_name}", "fio"),
                     ("Эл. почта", user.email, "email")]
        if user.class_number >= 10:
            for_modal.append(("Класс поступления", f"{user.class_number}, {user.profile_10_11} профиль", "grade"))
        else:
            for_modal.append(("Класс поступления", user.class_number))
        for_modal.extend(
            [("Дата рождения", user.birth_date, "birthday"), ("Статус участия", statuses[user.status], "status"),
             ("Школа", user.school, "school"),
             ("Контакты родителя",
              f"{user.parent_surname} {user.parent_name} {user.parent_third_name}, {user.parent_phone_number}",
              "parent")])
        exams = db_sess.query(Invite).filter(Invite.user_id == user.id).order_by(desc(Invite.made_on)).all()
        for_exam = []
        kwargs["res_opt"] = json.load(open('py_scripts/consts/results.json', mode='rb'))
        for exam in exams:
            exam_description = exam.parent_exam.exam_description if exam.parent_exam.exam_description else "Не указано"
            result = kwargs["res_opt"][exam.result]
            result_description = exam.result_description if exam.result_description else "Не указано"
            for_exam.append({"ID": str(exam.exam_id), "Название экзамена": exam.parent_exam.title,
                             "Дата": exam.parent_exam.date.strftime("%d/%m/%Y %H:%M:%S"),
                             "Описание экзамена": exam_description,
                             "Результат": result,
                             "Описание результата": result_description})
        kwargs["user_info"] = [for_modal, for_exam, user.id]
        return render_template('cabinet_for_admin.html',
                               **generate_data_for_base("/users/<user_id>", title="Личный кабинет поступающего"),
                               **kwargs)

    @staticmethod
    @login_required
    @non_admin_forbidden
    def update_result():
        try:
            if request.method == 'POST':
                value = request.form['value']
                edit_id = request.form['id']
                user_id = request.form['user_id']
                print(value, edit_id, user_id)
                db_sess = db_session.create_session()
                invite = db_sess.query(Invite).filter(
                    and_(Invite.exam_id == edit_id, Invite.user_id == user_id)).first()
                invite.result_description = value
                invite.edited_on = datetime.datetime.now()
                db_sess.commit()
                db_sess.close()

                success = 1
                return jsonify(success)
        except Exception as e:
            print(e)
