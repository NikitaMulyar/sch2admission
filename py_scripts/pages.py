import datetime
import json
import os

import markdown
from flask import render_template, request, make_response, redirect, abort, jsonify
from flask_login import current_user, login_required
from sqlalchemy import desc, and_

from py_scripts.forms import ExamCreateForm
from py_scripts.forms import ExamStatusesForm
from py_scripts.forms import InvitesForm, NotesForm
from py_scripts.funcs_back import generate_data_for_base, status_changed_notif, mailing_invites, INVITES_PROCESS
from py_scripts.funcs_back import mailing_posts
from sa_models import db_session
from sa_models.exams import Exam
from sa_models.invites import Invite
from sa_models.notes import Note
from sa_models.notifications import Notification
from sa_models.users import User


def must_fill_these_fields():
    notif = Notification(
        user_id=current_user.id,
        type='warn',
        text='Сначала необходимо дозаполнить эти поля!'
    )
    notif.set_str_date()
    db_sess = db_session.create_session()
    db_sess.add(notif)
    db_sess.commit()
    db_sess.close()


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
        app.add_endpoint('/applications', 'back_applications', self.back_applications)
        app.add_endpoint('/application/<int:user_id>/<action>', 'back_application_action', self.back_application_action)
        app.add_endpoint('/inviting/<step>', 'back_inviting', self.back_inviting, methods=['GET', 'POST'])
        app.add_endpoint('/inviting', 'back_inviting_handler', self.back_inviting_handler)
        app.add_endpoint('/inviting/end/end', 'back_inviting_end_setting', self.back_inviting_end_setting)
        app.add_endpoint('/newnote', 'back_post_creating', self.back_post_creating, methods=['GET', 'POST'])
        app.add_endpoint('/editnote/<int:note_id>', 'back_post_editing', self.back_post_editing,
                         methods=['GET', 'POST'])
        app.add_endpoint('/deletenote/<int:note_id>', 'back_post_deleting', self.back_post_deleting)
        app.add_endpoint('/users/<user_id>', 'user_info_for_admin', self.user_info_for_admin, methods=['GET', 'POST'])
        app.add_endpoint('/update', 'update_result', self.update_result, methods=["POST"])

    @staticmethod
    def admin_forbidden(func):
        def wrapper(*args, **kwargs):
            if current_user.role == 'admin':
                return redirect('/')
            return func(*args, **kwargs)

        return wrapper

    @staticmethod
    def non_admin_forbidden(func):
        def wrapper(*args, **kwargs):
            if current_user.role != 'admin':
                return redirect('/')
            return func(*args, **kwargs)

        return wrapper

    @staticmethod
    def back_index():
        server_data = request.cookies.get("server_data", '')
        db_sess = db_session.create_session()
        notes = db_sess.query(Note).order_by(Note.made_on.desc()).all()
        arr = []
        for note in notes:
            classes = json.load(open(note.path_show_config, mode='rb'))
            if (current_user.is_authenticated and [current_user.class_number, current_user.profile_10_11] in classes or
                    len(classes) == 12 or current_user.role == 'admin'):
                edited_on = note.edit_on
                if edited_on:
                    edited_on = edited_on.strftime('%H:%M, %d.%m.%Y')
                made_on = note.made_on.strftime('%H:%M, %d.%m.%Y')
                arr.append(
                    [note.id, note.title, markdown.markdown(note.text), made_on,
                     edited_on, f'{note.author.name} {note.author.surname}']
                )
        db_sess.close()
        resp = make_response(render_template('index.html', notes=arr,
                                             **generate_data_for_base(user_id=server_data)))
        resp.set_cookie("server_data", server_data, max_age=0)
        return resp

    @staticmethod
    @login_required
    @non_admin_forbidden
    def back_post_creating():
        form = NotesForm.get_form()
        if form.validate_on_submit():
            classes_chosen = []
            for class_ in form.classes_ids:
                ex_ = form.__getattribute__(f"class_{class_}")
                if ex_.data:
                    classes_chosen.append(f"class_{class_}")
            if len(classes_chosen) == 0:
                form.for_everyone.errors.append('Необходимо выбрать хотя бы один класс.')
            else:
                arr = []
                profiles = json.load(open("py_scripts/consts/profiles.json", mode='rb'))
                for class_ in classes_chosen:
                    s = class_.split('_')
                    if len(s) == 2:
                        arr.append([int(s[1]), 'Общий'])
                    else:
                        arr.append([int(s[1]), profiles[int(s[2])]])
                db_sess = db_session.create_session()
                note = Note(
                    author_id=current_user.id,
                    title=form.title.data,
                    text=form.text.data
                )
                notif = Notification(
                    user_id=current_user.id,
                    type='system',
                    text='Пост успешно опубликован!'
                )
                notif.set_str_date()
                db_sess.add(note)
                db_sess.add(notif)
                db_sess.commit()
                note_info = [note.id, note.title]
                json.dump(arr, open(f'admin_data/notes_config/note_{note_info[0]}.json', mode='w'))
                note.path_show_config = f'admin_data/notes_config/note_{note_info[0]}.json'
                db_sess.commit()
                db_sess.close()

                for_users_emails = []
                for_users_ids = []

                db_sess = db_session.create_session()
                users = db_sess.query(User).all()
                for user in users:
                    if [user.class_number, user.profile_10_11] in arr:
                        for_users_ids.append(user.id)
                        for_users_emails.append(user.email)

                if form.site_notification.data:
                    for user in for_users_ids:
                        notif = Notification(
                            user_id=user,
                            link=f'/#note-{note_info[0]}',
                            text=f'Новая публикация от приемной комиссии: <b>"{note_info[1]}"</b>'
                        )
                        notif.set_str_date()
                        db_sess.add(notif)

                    notif = Notification(
                        user_id=current_user.id,
                        type='system',
                        text=f'Рассылка на сайте произведена успешно!'
                    )
                    notif.set_str_date()
                    db_sess.add(notif)
                    db_sess.commit()

                if form.email_notification.data:
                    mailing_posts(for_users_emails, note_info)
                    notif = Notification(
                        user_id=current_user.id,
                        type='system',
                        text=f'Рассылка на электронную почту произведена успешно!'
                    )
                    notif.set_str_date()
                    db_sess.add(notif)
                    db_sess.commit()

                db_sess.close()
                return redirect('/')
        return render_template('note_creating_edtiting.html', form=form,
                               **generate_data_for_base('/newnote', 'Создание публикации'))

    @staticmethod
    @login_required
    @non_admin_forbidden
    def back_post_editing(note_id):
        db_sess = db_session.create_session()
        note = db_sess.query(Note).get(note_id)
        if not note:
            db_sess.close()
            abort(404)

        form = NotesForm.get_form()
        if form.validate_on_submit():
            classes_chosen = []
            for class_ in form.classes_ids:
                ex_ = form.__getattribute__(f"class_{class_}")
                if ex_.data:
                    classes_chosen.append(f"class_{class_}")
            if len(classes_chosen) == 0:
                form.for_everyone.errors.append('Необходимо выбрать хотя бы один класс.')
            else:
                arr = []
                profiles = json.load(open("py_scripts/consts/profiles.json", mode='rb'))
                for class_ in classes_chosen:
                    s = class_.split('_')
                    if len(s) == 2:
                        arr.append([int(s[1]), 'Общий'])
                    else:
                        arr.append([int(s[1]), profiles[int(s[2])]])
                note.title = form.title.data
                note.text = form.text.data
                note.edit_on = datetime.datetime.now()
                db_sess.commit()
                json.dump(arr, open(note.path_show_config, mode='w'))
                db_sess.close()
                return redirect('/')

        form.title.data = note.title
        form.text.data = note.text

        classes_chosen = json.load(open(note.path_show_config, mode='rb'))
        db_sess.close()
        profiles = json.load(open("py_scripts/consts/profiles.json", mode='rb'))
        arr = []
        for class_ in classes_chosen:
            if class_[1] not in profiles:
                arr.append(f'class_{class_[0]}')
            else:
                ind = profiles.index(class_[1])
                arr.append(f'class_{class_[0]}_{ind}')
        for class_ in form.classes_ids:
            ex_ = form.__getattribute__(f"class_{class_}")
            ex_.data = True
            form.__setattr__(f"class_{class_}", ex_)

        return render_template('note_creating_edtiting.html', form=form,
                               **generate_data_for_base('/edtinote', 'Редактирование публикации'))

    @staticmethod
    @login_required
    @non_admin_forbidden
    def back_post_deleting(note_id):
        db_sess = db_session.create_session()
        note = db_sess.query(Note).get(note_id)
        if not note:
            db_sess.close()
            abort(404)

        if os.path.exists(note.path_show_config):
            os.remove(note.path_show_config)
        db_sess.delete(note)
        db_sess.commit()
        notif = Notification(
            user_id=current_user.id,
            type='system',
            text='Запись успешно удалена.'
        )
        notif.set_str_date()
        db_sess.commit()
        db_sess.close()
        return redirect('/')

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
    @login_required
    @admin_forbidden
    def back_invites():
        db_sess = db_session.create_session()
        invites = sorted(db_sess.query(User).get(current_user.id).invites,
                         key=lambda inv: inv.parent_exam.date, reverse=True)
        arr = []
        for inv in invites:
            arr.append([inv.parent_exam.title, inv.parent_exam.date.strftime('%H:%M, %d.%m.%Y'),
                        inv.parent_exam.exam_description])
        return render_template('invites.html', **generate_data_for_base('/invites',
                                                                        'Приглашения на вступительные испытания'),
                               invites=arr)

    @staticmethod
    @login_required
    @admin_forbidden
    def back_results():
        results = json.load(open('py_scripts/consts/results.json', mode='rb'))
        db_sess = db_session.create_session()
        invites = sorted(db_sess.query(User).get(current_user.id).invites,
                         key=lambda inv: inv.parent_exam.date, reverse=True)
        arr = []
        for inv in invites:
            if inv.result:
                arr.append([inv.parent_exam.title, inv.parent_exam.date.strftime('%H:%M, %d.%m.%Y'),
                            results[inv.result], inv.result_description, inv.result])
            else:
                arr.append([inv.parent_exam.title, inv.parent_exam.date.strftime('%H:%M, %d.%m.%Y'),
                            '-', '-', inv.result])
        return render_template('results.html', **generate_data_for_base('/results',
                                                                        'Результаты вступительных испытаний'),
                               invites=arr)

    @staticmethod
    def back_contacts():
        return render_template('contacts.html', **generate_data_for_base('/contacts',
                                                                         'Контакты'))

    @staticmethod
    @login_required
    @non_admin_forbidden
    def back_exams():
        db_sess = db_session.create_session()
        exams = db_sess.query(Exam).order_by(Exam.date.desc(), Exam.title, Exam.profile_10_11).all()
        exams_list = {6: [], 7: [], 8: [], 9: [], 10: [], 11: []}
        for exam in exams:
            arr = [exam.id, exam.title, exam.profile_10_11, exam.date.strftime("%H:%M, %d.%m.%Y")]
            exams_list[exam.for_class].append(arr)
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
                if form.title.data == 'Другое' and not form.new_title.data:
                    form.new_title.errors.append('Обязательное поле')
                else:
                    profile = 'Общий'
                    if form.class_number.data >= 10:
                        profile = form.profile.data
                    title = form.title.data
                    if title == 'Другое':
                        title = form.new_title.data
                    exam = Exam(
                        title=title,
                        date=form.date.data,
                        exam_description=form.exam_description.data,
                        for_class=form.class_number.data,
                        profile_10_11=profile
                    )
                    notif = Notification(
                        user_id=current_user.id,
                        text=f'Экзамен <b>"{title}"</b> успешно создан!',
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
                                                                                  'Создание вступительного испытания'),
                                   form=form)
        if exam_id == 'statuses':
            form = ExamStatusesForm()
            if form.validate_on_submit():
                statuses = json.load(open('py_scripts/consts/registration_status.json', mode='rb'))
                statuses['6-7'] = form.exams_6_7.data
                statuses['8-11'] = form.exams_8_11.data
                json.dump(statuses, open('py_scripts/consts/registration_status.json', mode='w'))
                notif = Notification(
                    user_id=current_user.id,
                    text=f'Настройки регистрации успешно обновлены!',
                    type='system'
                )
                notif.set_str_date()
                db_sess = db_session.create_session()
                db_sess.add(notif)
                db_sess.commit()
                db_sess.close()
                return redirect('/exams')
            return render_template('manage_exams_statuses.html',
                                   **generate_data_for_base('/exams/statuses',
                                                            'Настройка регистрации на вступительные испытания'),
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
                                        statuses[el.status], for_modal, for_exam, el.id, el.photo_path])

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

    @staticmethod
    @login_required
    @non_admin_forbidden
    def back_applications():
        db_sess = db_session.create_session()
        all_applies = (db_sess.query(User).filter(User.status == "4", User.role != 'admin')
                       .order_by(User.reg_date).all())
        user_list = []
        for user in all_applies:
            arr = [
                user.photo_path,
                f'{user.surname} {user.name} {user.third_name}'
            ]
            data = [
                ("Эл. почта", user.email),
                ("Дата рождения", user.birth_date.strftime('%d.%m.%Y')),
                ("Поступает в",
                 f"{user.class_number} {user.profile_10_11.lower() if user.class_number >= 10 else ''} класс"),
                ("Школа", user.school),
                ("Родитель", f"{user.parent_surname} {user.parent_name} {user.parent_third_name}"),
                ("Телефон", user.parent_phone_number),
                ("О себе", user.about if user.about else '-'),
                ("Родственники в Л2Ш", user.family_friends_in_l2sh if user.family_friends_in_l2sh else '-')
            ]
            arr.append(data)
            arr.extend([user.reg_date.strftime('%H:%M, %d.%m.%Y'), user.id])
            user_list.append(arr)
        db_sess.close()
        return render_template('applications.html', **generate_data_for_base('/applications',
                                                                             'Заявки на участие в конкурсе'),
                               user_list=user_list)

    @staticmethod
    @login_required
    @non_admin_forbidden
    def back_application_action(user_id, action):
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(user_id)
        if not user or not (action == 'approve' or action == 'reject'):
            abort(404)

        if action == 'approve':
            user.status = "0"
            txt = 'одобрена'
            clr = "#198754"
        else:
            user.status = "5"
            txt = 'отклонена'
            clr = "#dc3545"
        notif = Notification(
            user_id=current_user.id,
            type='system',
            text=f'Заявка поступающего <b>{user.surname} {user.name} {user.third_name}</b> {txt}.'
        )
        notif2 = Notification(
            user_id=user.id,
            text=f'Ваша заявка на участие в конкурсе <b style="color: {clr}">{txt.upper()}</b>!',
            link='/lk'
        )
        notif.set_str_date()
        notif2.set_str_date()
        db_sess.add(notif)
        db_sess.add(notif2)
        db_sess.commit()
        status_changed_notif(user.email, user.name, user.surname, f'<b style="color: {clr}">{txt.upper()}</b>')
        db_sess.close()
        return redirect('/applications')

    @staticmethod
    @login_required
    @non_admin_forbidden
    def back_inviting_handler():
        return redirect('/inviting/1')

    @staticmethod
    @login_required
    @non_admin_forbidden
    def back_inviting(step):
        steps = ['1', '2', 'a1', 'a2', 'm']
        if step not in steps:
            abort(404)

        if request.method == "GET":
            path_ = f'admin_data/invites_config/invite_{current_user.id}.json'
            if not os.path.exists(path_):
                info = dict()
                info["CLASS"] = -1  # part 1
                info["PROFILE"] = ''  # part 1
                info["EXAM_ID_NEW"] = -1  # part 2
                info["EXAM_IDS_NEED"] = []  # part 2
                info["LIMIT"] = -1  # auto 1
                info["PRIORITY"] = -1  # auto 1
                info["TIMES_WRITTEN"] = []  # auto 1
                info["STUDENTS_IDS"] = []  # auto 2 / manual
                json.dump(info, open(path_, mode='w'))
            info = json.load(open(path_, mode='rb'))

            if step == '1':
                form = InvitesForm.get_part_1()
                if info["CLASS"] != -1:
                    form.class_number.data = info["CLASS"]
                if info["PROFILE"] != '' and info["PROFILE"] != 'Общий':
                    form.profile.data = info["PROFILE"]

                return render_template('inviting_form/part1.html',
                                       **generate_data_for_base('/inviting', 'Создание приглашений на '
                                                                             'вступительные испытания'),
                                       form=form)
            elif step == '2':
                if info['CLASS'] == -1 or info['PROFILE'] == '':
                    must_fill_these_fields()
                    return redirect('/inviting/1')

                form = InvitesForm.get_part_2(**info)
                if info["EXAM_ID_NEW"] != -1:
                    form.exam.data = info["EXAM_ID_NEW"]
                if info["EXAM_IDS_NEED"] != []:
                    for ex in info["EXAM_IDS_NEED"]:
                        form.__getattribute__(f'exam_need_{ex[0]}').data = True

                return render_template('inviting_form/part2.html',
                                       **generate_data_for_base('/inviting', 'Создание приглашений на '
                                                                             'вступительные испытания'),
                                       form=form)
            elif step == 'a1':
                if info['CLASS'] == -1 or info['PROFILE'] == '':
                    must_fill_these_fields()
                    return redirect('/inviting/1')

                if info['EXAM_ID_NEW'] == -1:
                    must_fill_these_fields()
                    return redirect('/inviting/2')

                form = InvitesForm.get_part_a1()
                if info["LIMIT"] != -1:
                    form.students_number.data = info["LIMIT"]
                if info["PRIORITY"] != -1:
                    form.priority.data = info["PRIORITY"]
                if info["TIMES_WRITTEN"] != []:
                    if 0 in info["TIMES_WRITTEN"]:
                        form.written_0_times.data = True
                    if 1 in info["TIMES_WRITTEN"]:
                        form.written_1_times.data = True
                    if 2 in info["TIMES_WRITTEN"]:
                        form.written_2_times.data = True

                return render_template('inviting_form/partA1.html',
                                       **generate_data_for_base('/inviting', 'Создание приглашений на '
                                                                             'вступительные испытания'),
                                       form=form)
            elif step == 'a2':
                if info['CLASS'] == -1 or info['PROFILE'] == '':
                    must_fill_these_fields()
                    return redirect('/inviting/1')

                if info['EXAM_ID_NEW'] == -1:
                    must_fill_these_fields()
                    return redirect('/inviting/2')

                if info['LIMIT'] == -1 or info['PRIORITY'] == -1 or info['TIMES_WRITTEN'] == []:
                    must_fill_these_fields()
                    return redirect('/inviting/a1')

                form = InvitesForm.get_part_a2(**info)
                return render_template('inviting_form/partA2.html',
                                       **generate_data_for_base('/inviting', 'Создание приглашений на '
                                                                             'вступительные испытания'),
                                       form=form)
            elif step == 'm':
                if info['CLASS'] == -1 or info['PROFILE'] == '':
                    must_fill_these_fields()
                    return redirect('/inviting/1')

                if info['EXAM_ID_NEW'] == -1:
                    must_fill_these_fields()
                    return redirect('/inviting/2')

                form = InvitesForm.get_part_m(**info)
                return render_template('inviting_form/partM.html',
                                       **generate_data_for_base('/inviting', 'Создание приглашений на '
                                                                             'вступительные испытания'),
                                       form=form)
        elif request.method == "POST":
            path_ = f'admin_data/invites_config/invite_{current_user.id}.json'
            if not os.path.exists(path_):
                return redirect('/inviting/1')
            info = json.load(open(path_, mode='rb'))

            if step == '1':
                form = InvitesForm.get_part_1()

                if form.validate_on_submit():
                    info['CLASS'] = form.class_number.data
                    info['PROFILE'] = 'Общий'
                    if info["CLASS"] >= 10:
                        info['PROFILE'] = form.profile.data
                    json.dump(info, open(path_, mode='w'))

                    return redirect('/inviting/2')
                return render_template('inviting_form/part1.html',
                                       **generate_data_for_base('/inviting', 'Создание приглашений на '
                                                                             'вступительные испытания'),
                                       form=form)
            elif step == '2':
                form = InvitesForm.get_part_2(**info)
                print(form.type_of_constructor.data)
                if form.validate_on_submit():
                    info['EXAM_ID_NEW'] = form.exam.data
                    info['EXAM_IDS_NEED'] = []
                    for ex_id in form.exams_need_ids:
                        ex_ = getattr(form, f'exam_need_{ex_id}')
                        if ex_.data:
                            info['EXAM_IDS_NEED'].append(ex_id)
                    json.dump(info, open(path_, mode='w'))

                    if form.type_of_constructor.data == 0:
                        return redirect('/inviting/a1')
                    return redirect('/inviting/m')
                return render_template('inviting_form/part2.html',
                                       **generate_data_for_base('/inviting', 'Создание приглашений на '
                                                                             'вступительные испытания'),
                                       form=form)
            elif step == 'a1':
                form = InvitesForm.get_part_a1()

                if form.validate_on_submit():
                    info['LIMIT'] = form.students_number.data
                    info['PRIORITY'] = form.priority.data
                    info['TIMES_WRITTEN'] = []
                    if form.written_0_times.data:
                        info["TIMES_WRITTEN"].append(0)
                    if form.written_1_times.data:
                        info["TIMES_WRITTEN"].append(1)
                    if form.written_2_times.data:
                        info["TIMES_WRITTEN"].append(2)

                    if len(info["TIMES_WRITTEN"]) == 0:
                        form.written_2_times.errors.append('Необходимо выбрать хотя бы один пункт в кол-ве попыток')
                        return render_template('inviting_form/partA1.html',
                                               **generate_data_for_base('/inviting', 'Создание приглашений на '
                                                                                     'вступительные испытания'),
                                               form=form)
                    json.dump(info, open(path_, mode='w'))

                    return redirect('/inviting/a2')
                return render_template('inviting_form/partA1.html',
                                       **generate_data_for_base('/inviting', 'Создание приглашений на '
                                                                             'вступительные испытания'),
                                       form=form)
            elif step == 'a2':
                form = InvitesForm.get_part_a2(**info)

                if form.validate_on_submit():
                    info['STUDENTS_IDS'] = []
                    for user_id in form.students_ids:
                        ex_ = getattr(form, f'student_{user_id}')
                        if ex_.data:
                            info['STUDENTS_IDS'].append(user_id)
                    json.dump(info, open(path_, mode='w'))

                    return redirect('/inviting/end/end')
                return render_template('inviting_form/partA2.html',
                                       **generate_data_for_base('/inviting', 'Создание приглашений на '
                                                                             'вступительные испытания'),
                                       form=form)
            elif step == 'm':
                form = InvitesForm.get_part_m(**info)

                if form.validate_on_submit():
                    info['STUDENTS_IDS'] = []
                    for user_id in form.students_ids:
                        ex_ = getattr(form, f'student_{user_id}')
                        if ex_.data:
                            info['STUDENTS_IDS'].append(user_id)
                    json.dump(info, open(path_, mode='w'))

                    return redirect('/inviting/end/end')
                return render_template('inviting_form/partM.html',
                                       **generate_data_for_base('/inviting', 'Создание приглашений на '
                                                                             'вступительные испытания'),
                                       form=form)

    @staticmethod
    @login_required
    @non_admin_forbidden
    def back_inviting_end_setting():
        path_ = f'admin_data/invites_config/invite_{current_user.id}.json'
        if not os.path.exists(path_) and not INVITES_PROCESS.get(current_user.id):
            return redirect('/inviting/1')
        if not os.path.exists(path_) and INVITES_PROCESS.get(current_user.id):
            if INVITES_PROCESS[current_user.id][2] == 0:
                INVITES_PROCESS.pop(current_user.id)
                return redirect('/inviting/1')

            db_sess = db_session.create_session()
            arr = []
            for email in INVITES_PROCESS[current_user.id][0]:
                user = db_sess.query(User).where(User.email == email).first()
                arr.append(
                    (f'{user.surname} {user.name} {user.third_name} ({user.email})', user.id)
                )
            db_sess.close()

            arr = sorted(arr, key=lambda a: a[0].split())
            data = [arr.copy(), INVITES_PROCESS[current_user.id][1]]

            if INVITES_PROCESS[current_user.id][1] == len(arr):
                INVITES_PROCESS[current_user.id][2] = INVITES_PROCESS[current_user.id][2] - 1

            return render_template('inviting_form/mailing_part.html',
                                   **generate_data_for_base('/inviting', 'Создание приглашений на '
                                                                         'вступительные испытания'),
                                   data=data)

        info = json.load(open(path_, mode='rb'))
        if info["STUDENTS_IDS"] == []:
            db_sess = db_session.create_session()
            notif = Notification(
                user_id=current_user.id,
                text=f'Вы не указали некоторые поля в форме. Проверьте, пожалуйста, ее еще раз.',
                type='warn'
            )
            notif.set_str_date()
            db_sess.add(notif)
            db_sess.commit()
            db_sess.close()
            return redirect('/inviting/1')

        db_sess = db_session.create_session()
        users = db_sess.query(User).filter(User.id.in_(info["STUDENTS_IDS"])).all()
        users_ = []
        for user in users:
            users_.append((user.email, f'{user.name} {user.surname}', user.id))
        exam = db_sess.query(Exam).get(info["EXAM_ID_NEW"])
        invite_description = '## Уважаемый(ая) {}!\n\n' + exam.exam_description
        exam = (exam.date.strftime('%d.%m'), exam.title)
        db_sess.close()
        mailing_invites(users_, invite_description, exam, current_user.id)
        os.remove(path_)

        data = [[], len(users_)]
        return render_template('inviting_form/mailing_part.html',
                               **generate_data_for_base('/inviting', 'Создание приглашений на '
                                                                     'вступительные испытания'),
                               data=data)
