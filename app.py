from flask import Flask, render_template, request, redirect, abort, url_for
from flask_login import LoginManager, login_user, current_user

from sa_models import db_session
from sa_models.users import User

import json
from py_scripts.forms import RegisterFormClasses6To9, RegisterFormClasses10To11, LoginForm


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
async def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
async def back_index():
    reg_stats = json.load(open('py_scripts/consts/registration_status.json', mode='rb'))
    return render_template('index.html', exams_on=reg_stats,
                           pic_url=url_for('static', filename='img/logo.png'))


@app.route('/login', methods=['GET', 'POST'])
async def back_login():
    if current_user.is_authenticated:
        return redirect('/')
    form = LoginForm()
    if form.validate_on_submit():
        return
    return render_template('login.html', form=form,
                           pic_url=url_for('static', filename='img/logo.png'))


@app.route('/register/<classes>', methods=['GET', 'POST'])
async def back_register(classes):
    if current_user.is_authenticated:
        return redirect('/')
    if classes == '6-9':
        form = RegisterFormClasses6To9()
    else:
        form = RegisterFormClasses10To11()
    if form.validate_on_submit():
        return
    reg_statuses = json.load(open('py_scripts/consts/registration_status.json', mode='rb'))
    if not reg_statuses.get(classes):
        abort(404)
    title = 'Регистрация на вступительные испытания в 6, 7, 8, 9 классы'
    if classes == '10-11':
        title = 'Регистрация на вступительные испытания в 10, 11 классы'
    return render_template('register.html', title=title,
                           exams_on=reg_statuses, form=form,
                           pic_url=url_for('static', filename='img/logo.png'))


if __name__ == '__main__':
    db_session.global_init('database/admission.db')
    app.run(port=8080, host='127.0.0.1')
