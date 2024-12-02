import datetime
import os

import markdown
from flask import render_template, request, make_response, redirect, abort
from flask_login import current_user, login_required
import json
from py_scripts.funcs_back import generate_data_for_base, status_changed_notif, mailing_invites, INVITES_PROCESS
from py_scripts.funcs_back import mailing_posts
from sa_models import db_session
from sa_models.exams import Exam
from sa_models.invites import Invite
from sa_models.notes import Note
from sa_models.notifications import Notification
from py_scripts.forms import ExamCreateForm, ExamStatusesForm
from py_scripts.forms import InvitesForm, NotesForm

from markupsafe import Markup

from sa_models.users import User


class EgePages:
    def __init__(self, app):
        app.add_endpoint('/ege/ict', 'ege_tasks', self.ege_tasks)

    @staticmethod
    def ege_tasks():
        return render_template('ege.html', **generate_data_for_base('ЕГЭ по информатике 2025'))
