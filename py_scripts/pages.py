import os

from flask import render_template, request, make_response, redirect, abort
from flask_login import current_user, login_required
import json
from py_scripts.funcs_back import generate_data_for_base, status_changed_notif, mailing_invites, INVITES_PROCESS
from sa_models import db_session
from sa_models.exams import Exam
from sa_models.invites import Invite
from sa_models.notifications import Notification
from py_scripts.forms import ExamCreateForm, ExamStatusesForm
from py_scripts.forms import InvitesForm

from markupsafe import Markup

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
        app.add_endpoint('/exams/<exam_id>', 'back_exam_info', self.back_exam_info, methods=['GET', 'POST'])
        app.add_endpoint('/applications', 'back_applications', self.back_applications)
        app.add_endpoint('/application/<int:user_id>/<action>', 'back_application_action', self.back_application_action)
        app.add_endpoint('/inviting/<step>', 'back_inviting', self.back_inviting, methods=['GET', 'POST'])
        app.add_endpoint('/inviting', 'back_inviting_handler', self.back_inviting_handler)
        app.add_endpoint('/inviting/end/end', 'back_inviting_end_setting', self.back_inviting_end_setting)

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
                                                                          'Создание нового вступительного испытания'),
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
        # МАТВЕЙ, ТУТ ТВОИ ОБРАБОТЧИКИ

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
                ("Поступает в", f"{user.class_number} {user.profile_10_11.lower() if user.class_number >= 10 else ''} класс"),
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
                info["CLASS"] = -1                 # part 1
                info["PROFILE"] = ''               # part 1
                info["EXAM_ID_NEW"] = -1           # part 2
                info["EXAM_IDS_NEED"] = []         # part 2
                info["LIMIT"] = -1                 # auto 1
                info["PRIORITY"] = -1              # auto 1
                info["TIMES_WRITTEN"] = []         # auto 1
                info["STUDENTS_IDS"] = []          # auto 2 / manual
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
