from time import sleep

import aiosmtplib
import smtplib
import asyncio
from email.mime.text import MIMEText
import markdown

import phonenumbers
from flask import request
from flask_login import current_user
from py_scripts.forms import RegisterFormClasses8To11, RegisterFormAdmins
from sa_models.exams import Exam
from sa_models.users import User
from sa_models.notifications import Notification
from sa_models.recovers import Recover
from sa_models import db_session
import os
import random
import json
from werkzeug.utils import secure_filename
from multiprocessing import Process, Manager

INVITES_PROCESS = {}


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


# ДЛЯ ПИСЕМ О СТАТУСЕ ЗАЯВКИ
def write_email_z(email, text, subj):
    attempts = 9
    while attempts > 0:
        try:
            smtpObj = smtplib.SMTP('smtp.yandex.ru', 587, timeout=90)
            smtpObj.starttls()
            break
        except Exception:
            attempts -= 1
            if attempts == 0:
                return
        sleep(10)
    config = json.load(open('py_scripts/consts/mailer.json', mode='rb'))
    smtpObj.login(config['login'], config['password'])
    mess = MIMEText(text, 'html')
    mess['From'] = config['mail']
    mess['To'] = email
    mess['Subject'] = subj
    smtpObj.sendmail(config['mail'], email, mess.as_string())
    smtpObj.quit()


def generate_and_send_password(email, name, surname, admin=False, third_name=None):
    psw_str = '23456789QWERTYUPASDFGHJKZXCVBNM'
    psw = "".join(random.choices(psw_str, k=8))
    if admin:
        email_text = (f'<h2>Уважаемый(-ая) {name} {third_name}!</h2>'
                      f'Ваш пароль от личного кабинета на сайте приемной кампании Лицея "Вторая Школа":'
                      f'<h3>{psw}</h3>'
                      f'Если Вы не подавали заявку на поступление, сообщите нам об этом по электронной почте: '
                      f'<a href="mailto:abitur@sch2.ru">abitur@sch2.ru</a>.<br><br>'
                      f'С уважением,<br>'
                      f'Лицей "Вторая Школа"')
    else:
        email_text = (f'<h2>Уважаемый(-ая) {name} {surname}!</h2>'
                      f'Ваша анкета для поступающих в Лицей "Вторая Школа" получена. Мы проверим Ваши данные и в течение '
                      f'трех рабочих дней отправим Вам письмо о статусе заявки.<br>'
                      f'Ваш пароль от личного кабинета на сайте приемной кампании Лицея "Вторая Школа":'
                      f'<h3>{psw}</h3>'
                      f'Если Вы не подавали заявку на поступление, сообщите нам об этом по электронной почте: '
                      f'<a href="mailto:abitur@sch2.ru">abitur@sch2.ru</a>.<br><br>'
                      f'С уважением,<br>'
                      f'Лицей "Вторая Школа"')
    asyncio.run(
        write_email(email, email_text, 'Заявка на участие во вступительных испытаниях в Лицей "Вторая Школа"')
    )
    return psw


def generate_and_send_password_recover(email, name, surname, admin=False, third_name=None):
    psw_str = '23456789QWERTYUPASDFGHJKZXCVBNM'
    psw = "".join(random.choices(psw_str, k=8))
    if admin:
        email_text = (f'<h2>Уважаемый(-ая) {name} {third_name}!</h2>'
                      f'Ваш новый пароль от личного кабинета на сайте приемной кампании Лицея "Вторая Школа":'
                      f'<h3>{psw}</h3><br>'
                      f'С уважением,<br>'
                      f'Лицей "Вторая Школа"')
    else:
        email_text = (f'<h2>Уважаемый(-ая) {name} {surname}!</h2>'
                      f'Ваш новый пароль от личного кабинета на сайте приемной кампании Лицея "Вторая Школа":'
                      f'<h3>{psw}</h3><br>'
                      f'С уважением,<br>'
                      f'Лицей "Вторая Школа"')
    asyncio.run(
        write_email(email, email_text, 'Сброс пароля на сайте приемной кампании Лицея "Вторая Школа"')
    )
    return psw


def register_user(request: request, form: RegisterFormClasses8To11, folder):
    try:
        psw = generate_and_send_password(form.email.data, form.name.data, form.surname.data)
    except Exception:
        return -1

    uploaded_file = request.files['photo']
    filename = f'{form.surname.data}_{form.name.data}_{form.third_name.data}_' + secure_filename(uploaded_file.filename)
    uploaded_file.save(os.path.join(folder, filename))
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
        photo_path=os.path.join(folder, filename),
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
        psw = generate_and_send_password(form.email.data, form.name.data, form.surname.data, admin=True,
                                         third_name=form.third_name.data)
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


def generate_data_for_base(title='Главная', user_id=''):
    reg_stats = json.load(open('py_scripts/consts/registration_status.json', mode='rb'))
    d = dict()
    d['exams_on'] = reg_stats
    # d['pic_url'] = url_for('static', filename='img/logo.png')
    d['pages'] = json.load(open('py_scripts/consts/pages.json', mode='rb'))
    d['admin_pages'] = json.load(open('py_scripts/consts/admin_pages.json', mode='rb'))
    d['title'] = title
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        d['notifications'] = sorted(db_sess.query(User).get(current_user.id).notifications, key=lambda a: a.made_on,
                                    reverse=True)
        for notif in d['notifications']:
            db_sess.delete(notif)
        if current_user.role == 'admin':
            d['application_number'] = (db_sess.query(User).filter(User.status == "4", User.role != 'admin')
                                       .count())
    elif user_id != '':
        d['notifications'] = (db_sess.query(Notification).where(Notification.user_id == int(user_id))
                              .order_by(Notification.made_on.desc()).all())
        for notif in d['notifications']:
            db_sess.delete(notif)
    db_sess.commit()
    db_sess.close()
    return d


def reset_password(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(user_id)
    try:
        psw = generate_and_send_password_recover(user.email, user.name, user.surname, admin=user.role == 'admin',
                                                 third_name=user.third_name)
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
                                       '"Вторая Школа"')
    )
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


def status_changed_notif(email, name, surname, ins_status):
    email_text = (f'<h2>Уважаемый(-ая) {name} {surname}!</h2>'
                  f'Статус Вашей заявки на сайте приемной кампании Лицея "Вторая Школа" обновился на "{ins_status}"!<br>'
                  f'Подробнее: http://127.0.0.1:8080/lk<br><br>'
                  f'С уважением,<br>'
                  f'Лицей "Вторая Школа"')
    p1 = Process(target=write_email_z, args=(email, email_text, 'Статус заявки на сайте приемной кампании Лицея '
                                                                '"Вторая Школа"'),
                 daemon=True)
    p1.start()


def mailing_wrapper(users: list, text: str, exam, arr: list):
    async def async_mailing(users: list, text: str, exam, arr: list):
        async def mailing(subj: str, email: str, text: str, arr: list, user_id):
            mess = MIMEText(markdown.markdown(text), 'html')
            mess['From'] = config['mail']
            mess['To'] = email
            mess['Subject'] = subj
            await smtpObj.sendmail(config['mail'], email, mess.as_string())
            arr.append(email)
            notif = Notification(
                user_id=user_id,
                text=subj,
                link='/invites'
            )
            notif.set_str_date()
            db_sess.add(notif)

        config = json.load(open('py_scripts/consts/mailer.json', mode='rb'))
        smtpObj = aiosmtplib.SMTP(hostname='smtp.yandex.ru', port=587, timeout=60,
                                  username=config['login'], password=config['password'],
                                  validate_certs=False)
        await smtpObj.connect()
        db_sess = db_session.create_session()
        tasks = []
        for user in users:
            tasks.append(
                mailing(f'Приглашение на вступительное испытание {exam[0]} {exam[1]}',
                        user[0], text.format(user[1]), arr, user[2])
            )
        await asyncio.gather(*tasks)
        db_sess.commit()
        db_sess.close()
        await smtpObj.quit()

    db_session.global_init('database/admission.db')
    asyncio.run(async_mailing(users, text, exam, arr))


def mailing_invites(users: list, text: str, exam, user):
    INVITES_PROCESS[user] = [Manager().list(), len(users), 3]
    p = Process(target=mailing_wrapper, args=(users, text, exam, INVITES_PROCESS[user][0]), daemon=True)
    p.start()


def mailing_wrapper_posts(users: list, note):
    async def async_mailing(users: list, note):
        async def mailing(subj: str, email: str, text: str):
            mess = MIMEText(text, 'html')
            mess['From'] = config['mail']
            mess['To'] = email
            mess['Subject'] = subj
            await smtpObj.sendmail(config['mail'], email, mess.as_string())

        config = json.load(open('py_scripts/consts/mailer.json', mode='rb'))
        smtpObj = aiosmtplib.SMTP(hostname='smtp.yandex.ru', port=587, timeout=60,
                                  username=config['login'], password=config['password'],
                                  validate_certs=False)
        await smtpObj.connect()
        tasks = []
        link = f'http://127.0.0.1:8080/#note-{note[0]}'
        for user in users:
            tasks.append(
                mailing(f'Новая публикация от приемной комиссии: "{note[1]}"',
                        user, f'<h2>Добрый день!</h2>'
                              f'Для просмотра записи перейдите по ссылке: '
                              f'<h3><a href="{link}">{link}</a></h3>')
            )
        await asyncio.gather(*tasks)
        await smtpObj.quit()

    asyncio.run(async_mailing(users, note))


def mailing_posts(users, note):
    p = Process(target=mailing_wrapper_posts, args=(users, note), daemon=True)
    p.start()
