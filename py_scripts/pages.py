from flask import render_template, request, make_response, redirect
from flask_login import current_user, login_required
import json
from py_scripts.funcs_back import generate_data_for_base


class Pages:
    def __init__(self, app):
        app.add_endpoint('/', 'back_index', self.back_index)
        app.add_endpoint('/lk', 'back_cabinet', self.back_cabinet)
        app.add_endpoint('/invites', 'back_invites', self.back_invites)
        app.add_endpoint('/results', 'back_results', self.back_results)
        app.add_endpoint('/contacts', 'back_contacts', self.back_contacts)

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
        return render_template('cabinet.html', **generate_data_for_base('/lk', 'Личный кабинет'),
                               data=data)

    @staticmethod
    @login_required
    def back_invites():
        return render_template('invites.html', **generate_data_for_base('/invites',
                                                                        'Приглашения на вступительные испытания'))

    @staticmethod
    @login_required
    def back_results():
        return render_template('results.html', **generate_data_for_base('/results',
                                                                        'Результаты вступительных испытаний'))

    @staticmethod
    def back_contacts():
        return render_template('contacts.html', **generate_data_for_base('/contacts',
                                                                         'Контакты'))
