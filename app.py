import sqlite3
import base64
import json
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from flask import Flask, request, render_template, session, redirect, url_for
from flask_socketio import SocketIO, send, join_room, leave_room
from cryptography.fernet import Fernet
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
load_dotenv()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/data.db'
app.config['SECRET_KEY']= os.getenv("SECRETKEY")
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

#Classes
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    UserID = db.Column(db.Integer, primary_key=True)
    Username = db.Column(db.String(128), unique=True, nullable=False)
    Password = db.Column(db.String(128), nullable=False)
    Email = db.Column(db.String(128), unique=True, nullable=False)
    ProfilePicture=db.Column(db.String(128), nullable=False, default='data:image/png;base64,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wF36r//6r9vb2++//36r1cLBkjQlVj1K+5YYtsS/juN4qE2MDLVWq/X7/f/8z//87rvvZmZmUH4VMems0cSaPaMJhWNEwdJDVVXbtsVTkKap4zitVuvu3budTufGjRuLi4tIrPR9H3vzoR0I0JT70MYApP0aHBaWZYVhmCTJ9vb2559/vr+/3263TdN0XRerM13XcRaMnowy2ocfflj2GMhzEEs+224WO1kMw2i320dHR998800YhnNzc4jUyjawrI+gLO1AI2hRDfg10CDa87w///nP//7v/56m6czMTBiGBwcHkBjEpGUn21CPOzI60OIYUSTOImV+ICW2bUdR1Ov1HMexbfvOnTs//PDDpUuX1tbWGo2GZGej1E2Jdr78aykRmiRJv9//7rvvvvnmm8PDw3a7rShKr9fTNG1ychJCg4rN0ky32smyYw0tjhHF931N02zbxuIfNxLW/zBDICsoF/bw4cNut6uqKvKmkAkyCs5FifLEcXz//v0vvvgC3adQLVHaREBfIBNJkliWhU19uAhlnwR5DspHH31U9hjIawBdRebm5i5cuHDu3DlYHIjXitNUDpZH+tArL+lc+9wDnvs5eFGCPug4dffu3b29PWRnvIGzJ0XDpUpFsG3b9/0nT548e/bs7t27i4uL586dwxJAzBO5w6UxmgiKvPXcPnJZ3ZGULWm8KIfJH6Ks2cHBwf3797e3t589e+Z5HgwoLj2qAYWjIsCViOaSu7u7T58+/f7776enp69du2YYBt560Q2flZUh2+T4fxkSmmyiGlyzYRiGYXj79u1Op3NwcAAro16vs7VllaBwVAdJykay9v7+fqfTefDgwczMzOrq6sLCwuTkpNT1gE8hqyZDivDcD5eQDX5GJ20cEEXRwcHBkydPHj58iLZJ8LMYhiFRIW6HrwwUjoqgqiqKViCtw3EcvO77/u7u7o8//qhpWrPZnJ+fX1xcnJ6ebrVa2SbY+OHl9/bQW/i12+12Op3t7e3d3d1eryfxY9QBgKAg/RyGD4t3VQMKR0WQAmJYraDTapIkjUYDuWRRFHW73W63u7W1pWna7OysZVkTExOtVmtiYqLRaDiOg211xz2pEJQgCFzX7ff7R0dHh4eHR0dHvu8/ffpUNtrpuo7kd0VR+v0+cjdUVXUcB+YJ62hUBgpHRUB29tBWN8MwXNeFEAz1an74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')
    SessionID = db.Column(db.String(128), nullable=False)
    
    def setpassword(self, password):
        self.Password=generate_password_hash(password)

    def checkpassword(self, password):
        return check_password_hash(self.Password, password)

with app.app_context():
    db.create_all()




@socketio.on('connect')
def handleconnection():
    sid = request.sid
    userid = session['user_id']
    con = sqlite3.connect('database/data.db')
    con.cursor().execute(f"UPDATE users SET sessionid= '{sid}' WHERE UserID={userid}")
    con.commit()
    con.close()

@socketio.on('joinroom')
def joinroom(room):
    join_room(str(room))
    session['room_id']=room

@socketio.on('leaveroom')
def leaveroom(b):
    leave_room(str(b))

@socketio.on('newroom')
def newroom(users):
    members={}
    for i,v in enumerate(users):
        members.update({i:str(encrypt(v))})
    insertsql("INSERT INTO rooms (Messages, Members) VALUES (?, ?)", ("{}", json.dumps(members)))

@socketio.on('message')
def handlemessage(message):
    receiver = json.loads(message)['room']
    encryptedmessage = str(encrypt(json.loads(message)['message']))
    send(message, room=receiver)
    messages = sqlite3.connect('database/data.db').cursor().execute(f"SELECT Messages FROM rooms WHERE RoomID={receiver}").fetchone()[0]
    messages = json.loads(messages)
    messages.update({str(len(messages)): {"from": json.loads(message)['sender'], "text": encryptedmessage}})
    insertsql("UPDATE rooms SET Messages = ? WHERE RoomID = ?", (json.dumps(messages), receiver))
    roommembers=json.loads(sqlite3.connect('database/data.db').cursor().execute(f"SELECT Members FROM rooms WHERE RoomID={receiver}").fetchone()[0])
    for user in roommembers:
        if decrypt(roommembers[user][2:-1].encode("utf-8"))=="Jeremy AI" and json.loads(message)['sender']!="Jeremy AI":
            keys = ["AIzaSyDj1AltbH7wJ5-Wunwl1pxIFScWulWIrZg", "AIzaSyDHLuGDWchJx89MTS1Tvd4Wq66gZt8fHVM", "AIzaSyBb4p-2DkMEXDIH8PlEY3wF1GPw4qBbAjE"]
            client = genai.Client(api_key=keys[0])
            response = client.models.generate_content(
                model="models/gemini-2.5-flash-preview-04-17",
                config=types.GenerateContentConfig(
                    system_instruction="When returning text/numbers, use already-formatted utf-8 charcters such as x² instead of x^2 etc."),
                contents=json.loads(message)['message']
                )
            aimessage = {"message": str(response.text), "sender": 'Jeremy AI', "room": receiver}
            handlemessage(json.dumps(aimessage))
                    



    return "test"

@socketio.on("pfpupload")
def pfpupload(data):
    con = sqlite3.connect('database/data.db')
    con.cursor().execute(f"UPDATE users SET ProfilePicture='{data}' WHERE SessionID='{request.sid}'")
    con.commit()
    con.close()

@app.route('/', methods=['GET'])
def home():
    try:
        # displaying index.html with arguments containing the data of all restaurants
        return render_template('main.html',
                               # the part that will be caught if the user is not logged in
                               logged_in=session['logged_in'], username=session['username'])
    except KeyError: # if the user isnt logged in
        return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method=='GET':
        return render_template('login.html')
    else:
        for user in sqlite3.connect('database/data.db').cursor().execute("SELECT * FROM users").fetchall():
            if decrypt(user[1])==request.form['username'].lower():
                if decrypt(user[2])==request.form['password']:
                    session['logged_in']=True
                    session['user_id']=user[0]
                    session['username']=decrypt(user[1])
                    return redirect(url_for('home'))
                return render_template('login.html', error="Incorrect Password")
        return render_template('login.html', error="User not found")
    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method=='GET':
        return render_template('signup.html')
    else:
        if len(request.form['username'])>0 and len(request.form['password'])>0:
            for user in sqlite3.connect('database/data.db').cursor().execute("SELECT * FROM users").fetchall():
                if decrypt(user[3])==request.form['email'] or decrypt(user[1])==request.form['username']:
                    return render_template('signup.html', error="Username or email already exists")
            username = encrypt(request.form['username'].lower())
            password = encrypt(request.form['password'])
            email = encrypt(request.form['email'].lower())
            insertsql("INSERT INTO users(Username, Password, Email) VALUES (?, ?, ?)",
                  (username, password, email))
            return redirect(url_for('login'))
        

@app.route('/api', methods=['GET'])
def api():
    userid = session['user_id']
    username = session['username']
    data = request.args.get('data')
    room = request.args.get('room')
    if data=="friends":
        #get users that have existing chats with the user
        chats={}
        for room in sqlite3.connect('database/data.db').cursor().execute("SELECT * FROM rooms").fetchall():
            users1 = []
            for encrypted_user in json.loads(room[2]):
                a = json.loads(room[2])[encrypted_user][2:-1].encode("utf-8")
                users1.append(decrypt(a))
            if username in users1:
                users = {}
                for i in json.loads(room[2]):
                    b = json.loads(room[2])[i][2:-1].encode("utf-8")
                    if decrypt(b)!=username:
                        for u in sqlite3.connect('database/data.db').cursor().execute("SELECT * FROM users").fetchall():
                            if decrypt(u[1])==decrypt(b).lower():   
                                users.update({"username": decrypt(b), "profile": u[4]})
                chats.update({room[0]: users})
        return chats
    elif data=="allusers":
        #get all users
        users = []
        for user in sqlite3.connect('database/data.db').cursor().execute(f"SELECT * FROM users WHERE UserID!={userid}").fetchall():
            users.append({"username": decrypt(user[1]), "profile": user[4]})
        return users
    elif data=="messages":
        messagedict={}
        messages = json.loads(sqlite3.connect('database/data.db').cursor().execute(f"SELECT Messages FROM rooms WHERE RoomID={room}").fetchone()[0])
        for message in messages:
            messagedict.update({str(message): {"from": messages[message]['from'], "text": decrypt(messages[message]['text'][2:-1].encode("utf-8"))}})
        return messagedict
    elif data=="pfp":
        pfp = sqlite3.connect("database/data.db").cursor().execute(f"SELECT ProfilePicture FROM users WHERE UserID={userid}").fetchone()
        return pfp[0]
            
    return "NULL"


def insertsql(query, values):
    '''function to simplify sql queries that insert into a table'''
    con = sqlite3.connect('database/data.db')
    cur = con.cursor()
    # executing the inputted query
    cur.execute(query, values)
    con.commit()
    con.close()

def encrypt(message):
    key = base64.b64encode(f"{app.secret_key:<32}".encode("utf-8"))
    encrypted = Fernet(key=key).encrypt(str(message).encode("utf-8"))
    return encrypted


def decrypt(cipher):
    key = base64.b64encode(f"{app.secret_key:<32}".encode("utf-8"))
    decrypted = Fernet(key=key).decrypt(cipher).decode("utf-8")
    return decrypted

def blob(string):
    return string[6:-5].encode("utf-8")
if __name__ == '__main__':
     socketio.run(app, debug=True)
