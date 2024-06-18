from flask import Flask, render_template, request, redirect, abort, url_for
from flask_login import LoginManager, login_user, current_user, login_required, logout_user

from sa_models import db_session
from sa_models.users import User

import json
from py_scripts.forms import RegisterFormClasses6To9, RegisterFormClasses10To11, LoginForm
from py_scripts.funcs_back import register_user, generate_data_for_base


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
    return render_template('index.html', **generate_data_for_base())


@app.route('/login', methods=['GET', 'POST'])
def back_login():
    if current_user.is_authenticated:
        return redirect('/')

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
    return render_template('login.html', form=form, **generate_data_for_base('/login',
                                                                             'Авторизация'))


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/register/<classes>', methods=['GET', 'POST'])
def back_register(classes):
    if current_user.is_authenticated:
        return redirect('/')

    reg_statuses = json.load(open('py_scripts/consts/registration_status.json', mode='rb'))
    if not reg_statuses.get(classes):
        abort(404)

    title = 'Регистрация на вступительные испытания в 6, 7, 8, 9 классы'
    if classes == '10-11':
        title = 'Регистрация на вступительные испытания в 10, 11 классы'
    if classes == '6-9':
        form = RegisterFormClasses6To9()
    else:
        form = RegisterFormClasses10To11()

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user_exist = db_sess.query(User).where(User.email == form.email.data).first()
        if user_exist:
            db_sess.close()
            form.email.errors.append('Пользователь с такой эл. почтой уже существует.')
        else:
            db_sess.close()
            res = register_user(request, form)
            if res == 0:
                return redirect('/login')
            form.email.errors.append('Не получилось отправить письмо с паролем на указанную почту.')
    return render_template('register.html', form=form,
                           **generate_data_for_base(f'/register/{classes}', title))


@app.route('/lk')
@login_required
def back_cabinet():
    return render_template('cabinet.html', **generate_data_for_base('/lk', 'Личный кабинет'))


@app.route('/invites')
@login_required
def back_invites():
    return render_template('invites.html', **generate_data_for_base('/invites',
                                                                    'Приглашения на экзамены'))


@app.route('/results')
@login_required
def back_results():
    return render_template('results.html', **generate_data_for_base('/results',
                                                                    'Результаты экзаменов'))


@app.route('/contacts', methods=['GET'])
def back_contacts():
    return render_template('contacts.html', **generate_data_for_base('/contacts',
                                                                     'Контакты'))


if __name__ == '__main__':
    db_session.global_init('database/admission.db')
    app.run(port=8080, host='127.0.0.1')
