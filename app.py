import sqlite3
import base64
import json
from flask import Flask, request, render_template, session, redirect, url_for
from flask_socketio import SocketIO, send, join_room, leave_room
from cryptography.fernet import Fernet
app = Flask(__name__)
# secret key is used to encrypt session storage data
app.secret_key = '6MT7DbpbBnGeOKC0HzthJVngnpBmne7v'
socketio = SocketIO(app, cors_allowed_origins="*")


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
    join_room(room)

@socketio.on('leaveroom')
def leaveroom(room):
    leave_room(room)

@socketio.on('newroom')
def newroom(users):
    members={}
    for i,v in enumerate(users):
        members.update({i:str(encrypt(v))})
    print(members)
    insertsql("INSERT INTO rooms (Messages, Members) VALUES (?, ?)", ("{}", json.dumps(members)))

@socketio.on('message')
def handlemessage(message):
    print(message)
    receiver = json.loads(message)['room']
    users = sqlite3.connect('database/data.db').cursor().execute("SELECT * FROM users").fetchall()
    encryptedmessage = encrypt(json.loads(message)['message'])
    send(message, room=receiver)
    insertsql("INSERT INTO messages (SenderID, ReceiverID, Message) VALUES (?, ?, ?)", (senderid, receiverid, encryptedmessage))
    return "test"

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
    if data=="friends":
        #get users that have existing chats with the user
        chats={}
        for room in sqlite3.connect('database/data.db').cursor().execute(f"SELECT * FROM rooms").fetchall():
            users1 = []
            for encrypted_user in json.loads(room[2]):
                a = json.loads(room[2])[encrypted_user][2:-1].encode("utf-8")
                users1.append(decrypt(a))
            if username in users1:
                users = []
                for i in json.loads(room[2]):
                    b = json.loads(room[2])[i][2:-1].encode("utf-8")
                    if decrypt(b)!=username:
                        users.append(decrypt(b))
                chats.update({room[0]: users})
        print(chats)
        return chats
    elif data=="allusers":
        #get all users
        users = []
        for user in sqlite3.connect('database/data.db').cursor().execute(f"SELECT * FROM users WHERE UserID!={userid}").fetchall():
            users.append({"username": decrypt(user[1]), "profile": user[4]})
        return users
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
