from flask import Flask, render_template, redirect, make_response, session, url_for, request
import requests
import sqlite3
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from forms.loginform import LoginForm
from forms.registerform import RegisterForm
from forms.roomform import CreateRoomForm

import datetime

from data.users import User
from data.rooms import Room
from data import db_session

import json


class Message:
    def __init__(self, text, author_id, sent_date=None):
        self.text = text
        self.author_id = author_id
        if sent_date is None:
            now = datetime.datetime.now()
            self.sent_date = now.strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.sent_date = sent_date
        try:
            db_sess = db_session.create_session()
            self.author = db_sess.query(User).get(author_id)
        finally:
            db_sess.close()


def get_room_messages(room_id):
    try:
        with open("data/rooms_id_messages.json", "r") as f:
            data = json.load(f)
            return data.get(str(room_id), [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


app = Flask(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=7
)
app.config['SECRET_KEY'] = "yandex_lyceum_secret_key"
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", title="Chattery - Main Page")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect("/")
        return render_template('login.html',
                               message="Wrong login or password.",
                               form=form)
    return render_template('login.html', title='Autorization', form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Registration',
                                   form=form,
                                   message="Passwords do not match.")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Registration',
                                   form=form,
                                   message="Such user already exists.")
        user = User(
            name=form.name.data,
            about=form.about.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/index')
    return render_template('register.html', title='Registration', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    rooms_dict = {}
    rooms_list = []
    col_am_list = []
    db_sess = db_session.create_session()
    try:
        with open("data/rooms_id_collaborators.json", "r", encoding="utf-8") as json_file:
            try:
                dict = json.load(json_file)
                for i in dict.keys():
                    try:
                        if user_id in dict[i]:
                            rooms_dict[f"{db_sess.query(Room).get(int(i))}"] = dict[i]
                            rooms_list.append(db_sess.query(Room).get(int(i)))
                            col_am_list.append(len(dict[i])) if dict[i] is not None else 0
                    except ValueError:
                        rooms_list = []
            except json.decoder.JSONDecodeError:
                rooms_list = []
                col_am_list = []

    except FileNotFoundError:
        print("JSON file for collaborators not found.")

    db_sess.close()

    return render_template("profile.html", title="Chattery - Profile",
                           user=db_sess.query(User).get(user_id),
                           rooms_list=rooms_list, collaborators_amount_list=col_am_list)


@app.route('/create_room', methods=["GET", "POST"])
@login_required
def create_room():
    form = CreateRoomForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(Room).filter(Room.label == form.label.data).first():
            return render_template("createroom.html", title="Chattery - Create a room", form=form,
                                   message="A room with such name already exists.")
        room = Room(
            label=form.label.data,
            about=form.about.data,
            collaborators=""  # щас в жсон переделать надобно
        )
        db_sess.add(room)
        db_sess.commit()
        try:
            with open("data/rooms_id_collaborators.json", "r+", encoding="utf-8") as json_file:
                try:
                    data = json.load(json_file)
                except json.decoder.JSONDecodeError:
                    data = {}
                data[f"{room.id}"] = [current_user.id]
            with open("data/rooms_id_collaborators.json", "w", encoding="utf-8") as json_file:
                json.dump(data, json_file)
        except FileNotFoundError:
            print("JSON file for collaborators not found.")
        room.collaborators = str(room.id)
        db_sess.commit()
        return redirect("/index")
    return render_template("createroom.html", title="Chattery - Create a room", form=form)


@app.route("/room/<int:room_id>")
@login_required
def show_room(room_id):
    db_sess = db_session.create_session()
    room = db_sess.query(Room).get(room_id)
    messages_list = []
    with open("data/rooms_id_messages.json", "r", encoding="utf-8") as json_file:
        try:
            messages_dict = json.load(json_file)
            print(messages_dict)
        except json.decoder.JSONDecodeError:
            print("json error")
            messages_dict = {}
    if str(room_id) in messages_dict.keys():
        for message_data in messages_dict[str(room_id)]:
            messages_list.append(Message(
                text=message_data[0],
                author_id=message_data[1],
                sent_date=message_data[2]
            ))
    return render_template("showroom.html", title=room.label, messages=messages_list, room=room)


@app.route("/room/<int:room_id>/collaborators")
def collaborators_list(room_id):
    db_sess = db_session.create_session()
    room = db_sess.query(Room).get(room_id)
    collab_list = []
    try:
        with open("data/rooms_id_collaborators.json", "r", encoding="utf-8") as json_file:
            rooms_dict = json.load(json_file)
        for collaborator_id in rooms_dict[str(room_id)]:
            collab_list.append(db_sess.query(User).get(collaborator_id))
    except FileNotFoundError:
        print("collaborators file not found")
    db_sess.close()
    return render_template("collaborators.html", title=f"{room.label} - Collaborators", room=room,
                           collab_list=collab_list, collab_list_len=len(collab_list))


@app.route("/room/<int:room_id>/options")
def room_options(room_id):
    db_sess = db_session.create_session()
    room = db_sess.query(Room).get(room_id)
    db_sess.close()
    return render_template("room_options.html", title=f"{room.label} - Options", room=room)

# ======================================================================================================================


@app.route("/handle_send_button/<int:room_id>", methods=["GET", "POST"])
@login_required
def handle_send_button(room_id):
    if True:
        messages_list = []
        messages_dict = {}
        with open("data/rooms_id_messages.json") as json_file:
            try:
                messages_dict = json.load(json_file)
                try:
                    for message_data in messages_dict[str(room_id)]:
                        messages_list.append(Message(
                            text=message_data[0],
                            author_id=message_data[1],
                            sent_date=message_data[2]
                        ))
                except KeyError:
                    messages_list = []
            except json.decoder.JSONDecodeError:
                messages_list = []
        db_sess = db_session.create_session()
        room = db_sess.query(Room).get(room_id)
        message = Message(
            text=request.form.get("message_inp"),
            author_id=current_user.id
        )
        with open("data/rooms_id_messages.json", "w", encoding="utf-8") as json_file:
            try:
                messages_dict[f"{room_id}"].append([message.text, message.author_id, message.sent_date])
            except KeyError:
                messages_dict[f"{room_id}"] = [[message.text, message.author_id, message.sent_date]]
            json.dump(messages_dict, json_file)
        db_sess.close()
        return redirect(f"/room/{room.id}")
    return render_template("showroom.html", title=room.label, messages=messages_list)


@app.route("/handle_add_collaborator/<int:room_id>", methods=["GET", "POST"])
@login_required
def add_collaborator(room_id):
    db_sess = db_session.create_session()
    room = db_sess.query(Room).get(room_id)
    user_id = int(request.form.get("user_input"))
    with open("data/rooms_id_collaborators.json", "r", encoding="utf-8") as json_file:
        try:
            collab_dict = json.load(json_file)
        except json.decoder.JSONDecodeError:
            collab_dict = {}
    user = db_sess.query(User).get(user_id)
    if user is not None:
        with open("data/rooms_id_collaborators.json", "w", encoding="utf-8") as json_file:
            if user_id not in collab_dict[str(room_id)]:
                collab_dict[str(room_id)].append(user_id)
            json.dump(collab_dict, json_file)
    else:
        return render_template("room_options.html", title=f"{room.label}", room=room,
                               message1="There is no such user.")
    return redirect(f"/room/{room_id}")


@app.route("/handle_delete_collaborator/<int:room_id>", methods=["GET", "POST"])
@login_required
def delete_collaborator(room_id):
    db_sess = db_session.create_session()
    room = db_sess.query(Room).get(room_id)
    user_id = request.form.get("user_input_delete")
    with open("data/rooms_id_collaborators.json", "r", encoding="utf-8") as json_file:
        try:
            collab_dict = json.load(json_file)
        except json.decoder.JSONDecodeError:
            collab_dict = {}
    user = db_sess.query(User).get(user_id)
    if user is not None:
        with open("data/rooms_id_collaborators.json", "w", encoding="utf-8") as json_file:
            if int(user_id) in collab_dict[str(room_id)]:
                collab_dict[str(room_id)].remove(int(user_id))
            else:
                return render_template("room_options.html", title=f"{room.label}", room=room,
                                       message2="There is no such user in this room")
            json.dump(collab_dict, json_file)
    else:
        return render_template("room_options.html", title=f"{room.label}", room=room,
                               message2="There is no such user.")
    return redirect(f"/room/{room_id}")


@app.route("/handle_delete_room/<int:room_id>", methods=["GET", "POST"])
@login_required
def delete_room(room_id):
    db_sess = db_session.create_session()
    room = db_sess.query(Room).get(room_id)
    db_sess.delete(room)
    db_sess.commit()
    db_sess.close()
    with open("data/rooms_id_collaborators.json", "r+", encoding="utf-8") as json_file:
        rooms_id_col = json.load(json_file)
        del rooms_id_col[str(room_id)]
        json_file.seek(0)
        json.dump(rooms_id_col, json_file)
        json_file.truncate()
    with open("data/rooms_id_messages.json", "r+", encoding="utf-8") as json_file:
        rooms_id_mes = json.load(json_file)
        del rooms_id_mes[str(room_id)]
        json_file.seek(0)
        json.dump(rooms_id_mes, json_file)
        json_file.truncate()
    return redirect(f"/profile/{current_user.id}")


@app.errorhandler(401)
def not_authorized(error):
    return render_template("not_authorized.html", title="Chattery - Not Authorized.")


if __name__ == "__main__":
    db_session.global_init("db/users.db")
    app.run("127.0.0.1", port=8081)
