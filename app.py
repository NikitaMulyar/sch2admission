from flask import Flask, render_template
from flask_login import LoginManager

from sa_models import db_session
from sa_models.users import User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    db_session.global_init('database/admission.db')
    app.run(port=8080, host='127.0.0.1')
