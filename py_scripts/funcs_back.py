import aiosmtplib
import asyncio
from email.mime.text import MIMEText

import phonenumbers
from flask import request, url_for
from flask_login import current_user, login_user
from py_scripts.forms import RegisterFormClasses8To11, RegisterFormAdmins
from sa_models.users import User
from sa_models.notifications import Notification
from sa_models.recovers import Recover
from sa_models import db_session
import os
import random
import json


async def write_email(email, text, subj):
    config = json.load(open('py_scripts/consts/mailer.json', mode='rb'))
    smtpObj = aiosmtplib.SMTP(hostname='smtp.yandex.ru', port=587, timeout=10,
                              username=config['login'], password=config['password'],
                              validate_certs=False)
    mess = MIMEText(text, 'html')
    mess['From'] = config['mail']
    mess['To'] = email
    mess['Subject'] = subj
    await smtpObj.connect()
    await smtpObj.sendmail(config['mail'], email, mess.as_string())
    await smtpObj.quit()


def generate_and_send_password(email, name, surname):
    psw_str = '23456789QWERTYUPASDFGHJKZXCVBNM'
    psw = "".join(random.choices(psw_str, k=8))
    email_text = (f'<h2>Уважаемый(-ая) {name} {surname}!</h2>'
                  f'Ваша анкета для поступающих в Лицей "Вторая Школа" получена. Мы проверим Ваши данные и в течение '
                  f'трех рабочих дней отправим Вам письмо о статусе заявки.<br>'
                  f'Ваш пароль от личного кабинета на сайте приемной кампании Лицея "Вторая Школа":'
                  f'<h3>{psw}</h3>'
                  f'Если Вы не подавали заявку на поступление, сообщите нам об этом по электронной почте: '
                  f'<a href="mailto:abitur@sch2.ru">abitur@sch2.ru</a>.<br><br>'
                  f'С уважением,<br>'
                  f'Лицей "Вторая Школа"')
    asyncio.run(write_email(email, email_text, 'Заявка на участие во вступительных испытаниях в Лицей "Вторая Школа"'))
    return psw


def generate_and_send_password_recover(email, name, surname):
    psw_str = '23456789QWERTYUPASDFGHJKZXCVBNM'
    psw = "".join(random.choices(psw_str, k=8))
    email_text = (f'<h2>Уважаемый(-ая) {name} {surname}!</h2>'
                  f'Ваш новый пароль от личного кабинета на сайте приемной кампании Лицея "Вторая Школа":'
                  f'<h3>{psw}</h3><br>'
                  f'С уважением,<br>'
                  f'Лицей "Вторая Школа"')
    asyncio.run(write_email(email, email_text, 'Сброс пароля на сайте приемной кампании Лицея "Вторая Школа"'))
    return psw


def register_user(request: request, form: RegisterFormClasses8To11):
    try:
        psw = generate_and_send_password(form.email.data, form.name.data, form.surname.data)
    except Exception:
        return -1

    uploaded_file = request.files['photo']
    type_ = uploaded_file.filename.split('.')[-1]
    file_path = os.path.join('abitur_data', 'photos',
                             f'{form.surname.data}_{form.name.data}_{form.third_name.data}.{type_}')
    uploaded_file.save(file_path)
    try:
        prof = form.profile.data
    except Exception:
        prof = 'Общий'
    num = phonenumbers.parse(form.parent_phone_number.data, 'RU')
    new_num = str(num.country_code) + str(num.national_number)
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
        parent_phone_number=new_num,
        photo_path=file_path,
        profile_10_11=prof,
        class_number=form.class_number.data,
        status="4"
    )
    user.set_password(psw)
    db_sess = db_session.create_session()
    db_sess.add(user)
    db_sess.commit()
    uid = str(user.id)
    new_notif = Notification(
        user_id=user.id,
        text='На Вашу почту выслано письмо с паролем от личного кабинета. Проверьте папку "Спам".',
        type='system'
    )
    new_notif.set_str_date()
    db_sess.add(new_notif)
    db_sess.commit()
    db_sess.close()
    return uid


def register_admin(form: RegisterFormAdmins):
    try:
        psw = generate_and_send_password(form.email.data, form.name.data, form.surname.data)
    except Exception:
        return -1

    user = User(
        email=form.email.data,
        name=form.name.data,
        surname=form.surname.data,
        third_name=form.third_name.data,
        role='admin'
    )
    user.set_password(psw)
    db_sess = db_session.create_session()
    db_sess.add(user)
    db_sess.commit()
    uid = str(user.id)
    new_notif = Notification(
        user_id=user.id,
        text='На Вашу почту выслано письмо с паролем от личного кабинета. Проверьте папку "Спам".',
        type='system'
    )
    new_notif.set_str_date()
    db_sess.add(new_notif)
    db_sess.commit()
    db_sess.close()
    return uid


def generate_data_for_base(current='/', title='Главная', user_id=''):
    reg_stats = json.load(open('py_scripts/consts/registration_status.json', mode='rb'))
    d = dict()
    d['exams_on'] = reg_stats
    d['pic_url'] = url_for('static', filename='img/logo.png')
    d['pages'] = json.load(open('py_scripts/consts/pages.json', mode='rb'))
    d['admin_pages'] = json.load(open('py_scripts/consts/admin_pages.json', mode='rb'))
    d['current'] = current
    d['title'] = title
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        d['notifications'] = sorted(db_sess.query(User).get(current_user.id).notifications, key=lambda a: a.made_on,
                                    reverse=True)
        for notif in d['notifications']:
            db_sess.delete(notif)
    elif user_id != '':
        d['notifications'] = sorted(db_sess.query(Notification).where(Notification.user_id == int(user_id)).all(),
                                    key=lambda a: a.made_on, reverse=True)
        for notif in d['notifications']:
            db_sess.delete(notif)
    db_sess.commit()
    db_sess.close()
    return d


def reset_password(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(user_id)
    try:
        psw = generate_and_send_password_recover(user.email, user.name, user.surname)
    except Exception:
        db_sess.close()
        return -1
    user.set_password(psw)
    new_notif = Notification(
        user_id=user_id,
        text=f'Пароль сброшен и выслан на Вашу эл. почту. Вы авторизованы как {user.email}.',
        type='system'
    )
    new_notif.set_str_date()
    db_sess.add(new_notif)
    db_sess.commit()
    db_sess.close()
    return 0


def generate_and_send_recover_link(email, name, surname, user_id):
    s = '0123456789QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm'
    code = "".join(random.choices(s, k=64))
    recover_link = f'http://127.0.0.1:8080/recover/{code}'

    email_text = (f'<h2>Уважаемый(-ая) {name} {surname}!</h2>'
                  f'Для восстановления пароля от личного кабинета на сайте приемной кампании Лицея "Вторая Школа" '
                  f'перейдите по ссылке:'
                  f'<h3><a href="{recover_link}">{recover_link}</a></h3>'
                  f'Если Вы не запрашивали восстановление пароля, ПРОИГНОРИРУЙТЕ это письмо!<br><br>'
                  f'С уважением,<br>'
                  f'Лицей "Вторая Школа"')
    asyncio.run(
        write_email(email, email_text, 'Восстановление пароля от личного кабинета на сайте приемной кампании Лицея '
                                       '"Вторая Школа"'))
    db_sess = db_session.create_session()
    rec = Recover(
        email=email,
        code=code
    )
    db_sess.add(rec)
    notif = Notification(
        user_id=user_id,
        text='На Вашу почту выслано письмо с ссылкой для восстановления пароля от личного кабинета. Проверьте папку '
             '"Спам".',
        type='system'
    )
    notif.set_str_date()
    db_sess.add(notif)
    db_sess.commit()
    db_sess.close()
