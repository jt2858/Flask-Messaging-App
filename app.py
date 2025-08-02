from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import InputRequired, Length, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, join_room, send
from dotenv import load_dotenv
from google import genai
from google.genai import types
import numpy as np
import os
import json
load_dotenv()
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

app.config['SECRET_KEY'] = os.getenv('SECRETKEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'database/data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# Initialize the login manager 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Classes
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    chats=db.Column(db.Text, nullable=False)
    picture = db.Column(db.Text, nullable=False, default=os.getenv("DEFAULTPFP"))
    session_id=db.Column(db.String(150), nullable=True)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    picture = db.Column(db.Text, nullable=True)
    messages = db.Column(db.Text, nullable=False)
    chat_type=db.Column(db.Text, nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(150), unique=True, nullable=False)
    chatid = db.Column(db.Integer, db.ForeignKey(Chat.id), nullable=False)

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    submit = SubmitField('create account')

    def validate_username(self, username):
        existing_user = User.query.filter(User.username.ilike(username.data)).first()
        if existing_user:
            raise ValidationError('That username already exists. Please choosemessagedifferent one.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('Remember Me')
    submit = SubmitField('continue')
 


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('messenger'))
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data
        password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=128)
        ai_chat = Chat(name=username+"'s AI", messages='{"0": {"from": "'+username+'\'s AI", "message": "Hello."}}', chat_type="AI", picture=os.getenv("AIPFP"))
        db.session.add(ai_chat)
        db.session.commit()
        new_user = User(username=username, password=password, chats=str(ai_chat.id))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('messenger'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(User.username.ilike(form.username.data)).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('messenger'))
        return render_template('login.html', form=form, error='Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('messenger'))
    return redirect(url_for('login'))


@app.route('/messenger', methods=['GET'])
@login_required
def messenger():
    existing_chats_arr=[]
    for chat in Chat.query.all():
        if chat.id in np.fromstring(current_user.chats, dtype=int, sep=","):
            chatname = chat.name
            if chat.chat_type!="AI": 
                chatnamearr = chatname.split(", ")
                for username in chatnamearr:
                    if username==current_user.username: chatnamearr.pop(chatnamearr.index(username))
                chatname = ", ".join(chatnamearr)
            existing_chats_arr.append([chatname, chat.messages, chat.picture, chat.id])
    if request.args.get("chatid"):
        if int(request.args.get("chatid")) not in np.fromstring(current_user.chats, dtype=int, sep=","):
            return redirect(url_for('messenger'))
        else:
            messages=[]
            try:
                for message in json.loads(Chat.query.filter_by(id=request.args.get("chatid")).first().messages).values():
                    try:
                        print(message['message'])
                        messages.append([message['from'], message['message'], message['file']])
                    except KeyError:
                        messages.append([message['from'], message['message']])
                return render_template('messenger.html', username=current_user.username, existing_chats=existing_chats_arr, message_history=messages)
            except AttributeError:
                return redirect(url_for("messenger"))
    return render_template('messenger.html', username=current_user.username, existing_chats=existing_chats_arr)


@app.route('/api', methods=['GET', 'POST'])
@login_required
def api():
    if request.args.get("usersearch"):
        users={}
        for user in enumerate(User.query.filter(User.username.contains(request.args.get("usersearch"))).all()):
            if user[1].username!=current_user.username: users.update({user[0]: {"username": user[1].username, "picture": user[1].picture}})
        return users
    if request.args.get("deletechat"):
        deletingchat = Chat.query.filter_by(id=request.args.get("deletechat")).first()
        if deletingchat.chat_type=="AI":
            return redirect(url_for("messenger"))
        for chat in np.fromstring(current_user.chats, dtype=int, sep=",").tolist():
            if deletingchat.id==chat:
                for user in User.query.all():
                    if int(deletingchat.id) in np.fromstring(user.chats, dtype=int, sep=",").tolist():
                        newchats = np.fromstring(user.chats, dtype=int, sep=",").tolist()
                        newchats.remove(deletingchat.id)
                        user.chats = ",".join(map(str, newchats))
                        db.session.delete(deletingchat)
                        db.session.commit()
        return redirect(url_for('messenger'))
    if request.args.get("createchat"):
        userarr = []
        userarr.append(current_user.username)
        for i in json.loads(request.get_json())['users']:
            userarr.append(i)
        chatname = ", ".join(userarr)
        newchat = Chat(name=chatname, messages='{}', chat_type="GROUP", picture=os.getenv("DEFAULTPFP"))
        db.session.add(newchat)
        for user in userarr:
            currentchats=np.fromstring(User.query.filter_by(username=user).first().chats, dtype=int, sep=",").tolist()
            currentchats.append(newchat.id)
            User.query.filter_by(username=user).first().chats=','.join(map(str, currentchats))
        db.session.commit()
    if request.args.get("username"):
        return User.query.filter_by(session_id=request.args.get("username")).first()
    return redirect(url_for("messenger"))

#SOCKETIO ROUTES
@socketio.on('connect')
def handle_connection():
    current_user.session_id=request.sid
    db.session.commit()
    for chat in np.fromstring(current_user.chats, dtype=int, sep=",").tolist():
        join_room(str(chat))


@socketio.on('message')
def handle_message(message):
    sender = User.query.filter_by(session_id=json.loads(message)['sender']).first().username if json.loads(message)['sender']!="AI" else "AI"
    chat = Chat.query.filter_by(id=json.loads(message)['room']).first()
    send(message, room=json.loads(message)['room'])
    messages = json.loads(chat.messages)
    messages.update({str(len(messages)): {"from": str(sender), "message": str(json.loads(message)['message'])}})
    chat.messages = json.dumps(messages)
    if chat.chat_type=="AI" and json.loads(message)['sender']!="AI":
        key = "AIzaSyDj1AltbH7wJ5-Wunwl1pxIFScWulWIrZg"
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            config=types.GenerateContentConfig(
                system_instruction="When returning text/numbers, use already-formatted utf-8 charcters such as x² instead of x^2 etc.the user's username is {}".format(sender)),
            contents=json.loads(message)['message']
            )
        aimessage = json.dumps({"message": str(response.text), "sender": "AI", "room": json.loads(message)["room"]})
        handle_message(aimessage)
    db.session.commit()

if __name__ == '__main__':
    socketio.run(app, debug=True)


