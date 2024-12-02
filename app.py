from flask import Flask, send_from_directory
from flask_login import LoginManager, login_required

from py_scripts.flask_wrapper import FlaskAppWrapper
from py_scripts.pages import Pages
from py_scripts.auth_class import AuthClass
from py_scripts.l2sh_project import EgePages
from sa_models import db_session
from sa_models.users import User
import ssl


ssl._create_default_https_context = ssl._create_unverified_context

app_fl = Flask(__name__)
db_session.global_init('database/admission2.db')
app_fl.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app_fl.config['UPLOAD_FOLDER'] = 'uploads'
login_manager = LoginManager()
login_manager.init_app(app_fl)

app = FlaskAppWrapper(app_fl)
pages = Pages(app)
auth = AuthClass(app)
ege_cl = EgePages(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app_fl.route(f'/{app.config["UPLOAD_FOLDER"]}/<name>')
@login_required
@pages.non_admin_forbidden
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1', debug=True)
