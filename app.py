from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user, login_user, login_required, logout_user

from string import ascii_letters, punctuation, digits

from data.db_session import create_session, global_init
from data.config import Config
from data.forms import LoginForm, RegisterForm
from data.models import User, Status

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)

global_init("db/data.db")
RUSSIAN_ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"


@login_manager.user_loader
def load_user(user_id):
    db_sess = create_session()
    user = db_sess.query(User).get(user_id)
    db_sess.close()
    return user


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    db_sess = create_session()

    form = RegisterForm()
    data = {
        'form': form,
        'message': None
    }

    if form.validate_on_submit():
        if db_sess.query(User).filter(User.login == form.login.data).first():
            data['message'] = "Такой пользователь уже есть."
        elif not all([symbol in RUSSIAN_ALPHABET + ' ' for symbol in form.fullname.data]):
            data['message'] = "Поле заполнено неверно. Используйте только буквы русского алфавита."
        elif not all([symbol in ascii_letters + digits for symbol in form.login.data]):
            data['message'] = "Логин содержит некорректные символы."
        elif not all(
                [symbol in ascii_letters + digits + punctuation for symbol in form.password.data]):
            data['message'] = "Пароль содержит некорректные символы."
        elif form.password.data != form.password_again.data:
            data['message'] = "Пароли не совпадают."
        else:
            user = User()

            user.fullname = ' '.join(list(map(lambda name: name.lower().capitalize(), form.fullname.data.split())))

            user.login = form.login.data.lower()
            user.set_password(form.password.data)

            db_sess.add(user)
            db_sess.commit()

            login_user(user, remember=True)
            db_sess.close()
            return redirect(url_for("profile"))
    return render_template('register.html', **data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    db_sess = create_session()

    form = LoginForm()
    data = {
        'form': form,
        'message': None
    }

    if form.validate_on_submit():
        # noinspection PyUnresolvedReferences
        user = db_sess.query(User).filter(User.login == form.login.data.lower()).first()

        if user:
            if user.check_password(form.password.data):  # noqa
                login_user(user, remember=form.remember_me.data)
                return redirect(url_for("profile"))

            data['message'] = 'Неверный пароль.'
        else:
            data['message'] = 'Неверный логин.'

    return render_template('login.html', **data)


@app.route('/')
@app.route('/home')
def index():
    return render_template("index.html")


@app.route('/my')
@login_required
def profile():
    db_sess = create_session()
    status = db_sess.query(Status).filter(Status.id == current_user.status).first()
    data = {
        "status": status
    }
    return render_template("profile.html", **data)


@app.route('/contact')
def contact():
    return render_template("contact.html")


if __name__ == '__main__':
    app.run()
