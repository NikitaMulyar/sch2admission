import smtplib
from email.mime.text import MIMEText
from flask import request, url_for
from py_scripts.forms import RegisterFormClasses10To11
from sa_models.users import User
from sa_models import db_session
import os
import random
import json


def write_email(email, text, subj):
    smtpObj = smtplib.SMTP('smtp.yandex.ru', 587, timeout=5)
    smtpObj.starttls()
    config = json.load(open('py_scripts/consts/mailer.json', mode='rb'))
    smtpObj.login(config['login'], config['password'])
    mess = MIMEText(text, 'html')
    mess['From'] = config['mail']
    mess['To'] = email
    mess['Subject'] = subj
    smtpObj.sendmail(config['mail'], email, mess.as_string())
    smtpObj.quit()


def register_user(request: request, form: RegisterFormClasses10To11):
    psw_str = '23456789QWERTYUPASDFGHJKZXCVBNM'
    psw = "".join(random.choices(psw_str, k=8))
    email_text = (f'<h3>Уважаемый(-ая) {form.name.data} {form.surname.data}!<br>'
                  f'Ваш пароль от личного кабинета на сайте приемной кампании Лицея "Вторая Школа":</h3>'
                  f'<h2>{psw}</h2>'
                  f'<h4>Если вы не регистрировались на этом сайте, ПРОИГНОРИРУЙТЕ это письмо!</h4>')
    try:
        write_email(form.email.data, email_text, 'Пароль от аккаунта на sch2admission.ru')
    except Exception:
        return -1

    uploaded_file = request.files['photo']
    type_ = uploaded_file.filename.split('.')[-1]
    file_path = os.path.join('abitur_data', 'photos', f'{form.surname.data}_{form.name.data}_{form.third_name.data}.{type_}')
    uploaded_file.save(file_path)
    try:
        prof = form.profile.data
    except Exception:
        prof = 'Общий'
    user = User(
        email=form.email.data,
        name=form.name.data,
        surname=form.surname.data,
        third_name=form.third_name.data,
        birth_date=form.birth_date.data,
        school=form.school.data,
        about=form.about.data,
        family_friends_in_l2sh=form.family_friends_in_l2sh.data,
        parent_name=form.parent_name.data,
        parent_surname=form.parent_surname.data,
        parent_third_name=form.parent_third_name.data,
        parent_phone_number=form.parent_phone_number.data,
        photo_path=file_path,
        profile_10_11=prof,
        class_number=form.class_number.data,
        status="4"
    )
    user.set_password(psw)
    db_sess = db_session.create_session()
    db_sess.add(user)
    db_sess.commit()
    db_sess.close()
    return 0


def generate_data_for_base(current='/', title='Главная'):
    reg_stats = json.load(open('py_scripts/consts/registration_status.json', mode='rb'))
    d = dict()
    d['exams_on'] = reg_stats
    d['pic_url'] = url_for('static', filename='img/logo.png')
    d['pages'] = json.load(open('py_scripts/consts/pages.json', mode='rb'))
    d['current'] = current
    d['title'] = title
    return d
