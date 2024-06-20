from flask import Flask
from flask_login import LoginManager

from py_scripts.flask_wrapper import FlaskAppWrapper
from py_scripts.pages import Pages
from py_scripts.auth_class import AuthClass
from sa_models import db_session
from sa_models.users import User


app_fl = Flask(__name__)
db_session.global_init('database/admission.db')
app_fl.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app_fl)

app = FlaskAppWrapper(app_fl)
pages = Pages(app)
auth = AuthClass(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
