import datetime

from flask import Flask, render_template, request, redirect, abort, make_response
from flask_login import LoginManager, login_user, current_user, login_required, logout_user

from sa_models import db_session
from sa_models.notifications import Notification
from sa_models.users import User
from sa_models.recovers import Recover

import json
from py_scripts.forms import (RegisterFormClasses6To7, RegisterFormClasses8To11, LoginForm, RecoverForm,
                              RegisterFormAdmins)
from py_scripts.funcs_back import (register_user, generate_data_for_base, generate_and_send_recover_link,
                                   reset_password,
                                   register_admin)

app = Flask(__name__)
db_session.global_init('database/admission.db')
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def back_index():
    server_data = request.cookies.get("server_data", '')
    resp = make_response(render_template('index.html', **generate_data_for_base(user_id=server_data)))
    resp.set_cookie("server_data", server_data, max_age=0)
    return resp


@app.route('/login', methods=['GET', 'POST'])
def back_login():
    if current_user.is_authenticated:
        return redirect('/')

    server_data = request.cookies.get("server_data", '')

    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user_exist = db_sess.query(User).where(User.email == form.email.data).first()
        if not user_exist:
            db_sess.close()
            form.email.errors.append('Пользователя с такой эл. почтой не найдено.')
        elif not user_exist.check_password(form.password.data):
            db_sess.close()
            form.password.errors.append('Неверный пароль. Забыли пароль?')
        else:
            login_user(user_exist, remember=form.remember_me.data)
            db_sess.close()
            return redirect('/')
    resp = make_response(render_template('login.html', form=form,
                                         **generate_data_for_base('/login', 'Авторизация',
                                                                  user_id=server_data)))
    resp.set_cookie("server_data", server_data, max_age=0)
    return resp


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    uid = str(current_user.id)
    new_notif = Notification(
        user_id=current_user.id,
        text='Вы вышли из личного кабинета.',
        type='system'
    )
    new_notif.set_str_date()
    db_sess = db_session.create_session()
    db_sess.add(new_notif)
    db_sess.commit()
    db_sess.close()
    resp = make_response(redirect("/"))
    resp.set_cookie("server_data", uid, max_age=60 * 60 * 24 * 365)
    logout_user()
    return resp


@app.route('/register/<classes>', methods=['GET', 'POST'])
def back_register(classes):
    if current_user.is_authenticated:
        return redirect('/')

    reg_statuses = json.load(open('py_scripts/consts/registration_status.json', mode='rb'))
    admin_link = open('py_scripts/consts/admin_registration_link.txt', mode='r', encoding='utf-8').read()
    if not reg_statuses.get(classes) and classes != admin_link:
        abort(404)

    if classes == admin_link:
        title = 'Регистрация администраторов в системе'
        form = RegisterFormAdmins()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            user_exist = db_sess.query(User).where(User.email == form.email.data).first()
            if user_exist:
                db_sess.close()
                form.email.errors.append('Пользователь с такой эл. почтой уже существует.')
            else:
                db_sess.close()
                res = register_admin(form)
                if res != -1:
                    resp = make_response(redirect('/login'))
                    resp.set_cookie("server_data", res, max_age=60 * 60 * 24 * 365)
                    return resp
                form.email.errors.append('Не получилось отправить письмо с паролем на указанную почту.')
        return render_template('admin_register.html', form=form,
                               **generate_data_for_base(f'/register/{classes}', title))

    title = 'Регистрация на вступительные испытания в 6, 7 классы'
    form = RegisterFormClasses6To7()
    if classes == '8-11':
        title = 'Регистрация на вступительные испытания в 8, 9, 10, 11 классы'
        form = RegisterFormClasses8To11()

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user_exist = db_sess.query(User).where(User.email == form.email.data).first()
        if user_exist:
            db_sess.close()
            form.email.errors.append('Пользователь с такой эл. почтой уже существует.')
        else:
            db_sess.close()
            res = register_user(request, form)
            if res != -1:
                resp = make_response(redirect('/login'))
                resp.set_cookie("server_data", res, max_age=60 * 60 * 24 * 365)
                return resp
            form.email.errors.append('Не получилось отправить письмо с паролем на указанную почту.')
    return render_template('register.html', form=form,
                           **generate_data_for_base(f'/register/{classes}', title))


@app.route('/recover/<code>', methods=['GET', 'POST'])
def back_recover(code):
    if current_user.is_authenticated:
        return redirect('/')

    if code == 'recover':
        server_data = request.cookies.get("server_data", '')

        form = RecoverForm()

        if form.validate_on_submit():
            db_sess = db_session.create_session()
            user_exist = db_sess.query(User).where(User.email == form.email.data).first()
            if not user_exist:
                db_sess.close()
                form.email.errors.append('Пользователя с такой эл. почтой не найдено.')
            else:
                try:
                    generate_and_send_recover_link(form.email.data, user_exist.name, user_exist.surname, user_exist.id)
                    resp = make_response(redirect('/login'))
                    resp.set_cookie("server_data", str(user_exist.id), max_age=60 * 60 * 24 * 365)
                    db_sess.close()
                    return resp
                except Exception:
                    form.email.errors.append(
                        'Не получилось отправить письмо с ссылкой для восстановления пароля на указанную почту.')
                db_sess.close()
        resp = make_response(render_template('recover.html', form=form,
                                             **generate_data_for_base(f'/recover/recover', 'Восстановление пароля',
                                                                      user_id=server_data)))
        resp.set_cookie("server_data", server_data, max_age=0)
        return resp

    db_sess = db_session.create_session()
    rec_code_exist = db_sess.query(Recover).where(Recover.code == code).first()

    if not rec_code_exist:
        db_sess.close()
        abort(404)

    user = db_sess.query(User).where(User.email == rec_code_exist.email).first()

    if datetime.datetime.now() > rec_code_exist.expiration_date:
        db_sess.delete(rec_code_exist)
        resp = make_response(redirect('/recover/recover'))
        resp.set_cookie("server_data", str(user.id), max_age=60 * 60 * 24 * 365)
        notif = Notification(
            user_id=user.id,
            text=f'Срок действия ссылки истек. Необходимо заново заполнить форму восстановления пароля.',
            type='warn'
        )
        notif.set_str_date()
        db_sess.add(notif)
        db_sess.commit()
        db_sess.close()
        return resp

    res = reset_password(user.id)

    db_sess.delete(rec_code_exist)
    if res == -1:
        resp = make_response(redirect('/recover/recover'))
        resp.set_cookie("server_data", str(user.id), max_age=60 * 60 * 24 * 365)
        notif = Notification(
            user_id=user.id,
            text=f'Не удалось отправить письмо с новым паролем на адрес {user.email}. Попробуйте снова.',
            type='warn'
        )
        notif.set_str_date()
        db_sess.add(notif)
        db_sess.commit()
        db_sess.close()
        return resp

    login_user(user)
    db_sess.commit()
    db_sess.close()
    return redirect('/')


@app.route('/lk')
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


@app.route('/invites')
@login_required
def back_invites():
    return render_template('invites.html', **generate_data_for_base('/invites',
                                                                    'Приглашения на вступительные испытания'))


@app.route('/results')
@login_required
def back_results():
    return render_template('results.html', **generate_data_for_base('/results',
                                                                    'Результаты вступительных испытаний'))


@app.route('/contacts', methods=['GET'])
def back_contacts():
    return render_template('contacts.html', **generate_data_for_base('/contacts',
                                                                     'Контакты'))


if __name__ == '__main__':
    db_session.global_init('database/admission.db')
    app.run(port=8080, host='127.0.0.1')
