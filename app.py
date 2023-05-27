from flask import Flask, render_template, redirect, url_for, abort
from flask_login import LoginManager, current_user, login_user, login_required, logout_user

from string import ascii_letters, punctuation, digits

from data.db_session import create_session, global_init
from data.config import Config
from data.forms import LoginForm, RegisterForm, AddMaterialForm
from data.models import User, Status, Material

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

            fullname = ' '.join(list(map(lambda name: name.lower().capitalize(), form.fullname.data.split())))

            if fullname == "Бакеева Римма Равилевна":
                user.status = 3

            user.fullname = fullname

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
                db_sess.close()
                return redirect(url_for("profile"))

            data['message'] = 'Неверный пароль.'
        else:
            data['message'] = 'Неверный логин.'

    db_sess.close()
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
    db_sess.close()
    return render_template("profile.html", **data)


@app.route('/contact')
def contact():
    return render_template("contact.html")


@app.route('/students')
@login_required
def students():
    if current_user.status < 3:
        abort(403)

    db_sess = create_session()
    users = db_sess.query(User).filter(User.status <= 2).all()  # noqa
    db_sess.close()

    data = {
        "students": users
    }

    return render_template("students.html", **data)


@app.route('/students/assign_status/<student_id>/<status_id>')
@login_required
def assign_status(student_id, status_id):
    if current_user.status < 3:
        abort(403)

    db_sess = create_session()
    user = db_sess.query(User).filter(User.id == student_id).first()
    user.status = int(status_id)
    db_sess.commit()
    db_sess.close()

    return redirect(url_for("students"))


@app.route('/<exam>/<subject>')
@login_required
def materials(exam, subject):
    if exam not in ("oge", "ege") or subject not in ("society", "history"):
        abort(404)

    title = f'{"ОГЭ" if exam == "oge" else "ЕГЭ"} по {"обществознанию" if subject == "society" else "истории"}'

    db_sess = create_session()
    regular_materials = db_sess.query(Material).filter(Material.exam == exam, Material.subject == subject,
                                                       Material.exclusive == False).all()  # noqa
    exclusive_materials = []
    if current_user.status >= 2:
        exclusive_materials = db_sess.query(Material).filter(Material.exam == exam, Material.subject == subject,
                                                             Material.exclusive == True).all()  # noqa
    db_sess.close()

    general_materials = list(
        sorted(exclusive_materials + regular_materials, key=lambda material: material.date_publish, reverse=True))

    data = {
        "exam": exam,
        "subject": subject,
        "materials": general_materials,
        "title": title
    }
    return render_template("materials.html", **data)


@app.route('/<exam>/<subject>/add_material', methods=['GET', 'POST'])
@login_required
def add_material(exam, subject):
    if exam not in ("oge", "ege") or subject not in ("society", "history"):
        abort(404)
    if current_user.status < 3:
        abort(403)

    form = AddMaterialForm()
    data = {
        "form": form
    }

    if form.validate_on_submit():
        db_sess = create_session()

        material = Material()

        material.title = form.title.data
        material.text = form.text.data
        material.exclusive = form.exclusive.data
        material.exam = exam
        material.subject = subject

        db_sess.add(material)
        db_sess.commit()
        db_sess.close()

        return redirect(url_for("materials", exam=exam, subject=subject))

    return render_template("add_material.html", **data)


@app.route('/<exam>/<subject>/delete_material/<material_id>')
@login_required
def delete_material(exam, subject, material_id):
    if exam not in ("oge", "ege") or subject not in ("society", "history"):
        abort(404)
    if current_user.status < 3:
        abort(403)

    db_sess = create_session()
    material = db_sess.query(Material).filter(Material.id == material_id).first()
    db_sess.delete(material)
    db_sess.commit()
    db_sess.close()

    return redirect(url_for("materials", exam=exam, subject=subject))


if __name__ == '__main__':
    app.run()
