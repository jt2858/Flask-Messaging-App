
# Flask Messaging Application with Real-time Chat and AI Integration
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
from PIL import Image
from io import BytesIO
from cryptography.fernet import Fernet
import numpy as np
import hashlib
import base64
import os
import json
# Load environment variables from .env file
load_dotenv()
# Initialize Flask app and SocketIO for real-time communication
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
# Application configuration

app.config['SECRET_KEY'] = os.getenv('SECRETKEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'database/data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect to login page for unauthorized access
# User loader function for Flask-Login

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login session management"""
    return User.query.get(int(user_id))

# Database Models
class User(db.Model, UserMixin):
    """User model for authentication and user data"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    chats=db.Column(db.Text, nullable=False)
    picture = db.Column(db.Text, nullable=False, default=os.getenv("DEFAULTPFP"))
    session_id=db.Column(db.String(150), nullable=True)

class Chat(db.Model):
    """Chat model for group and AI conversations"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    picture = db.Column(db.Text, nullable=True)
    messages = db.Column(db.Text, nullable=False)
    chat_type=db.Column(db.Text, nullable=False)

# WTForms for user authentication
class SignupForm(FlaskForm):
    """Form for user registration"""
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    submit = SubmitField('create account')

    def validate_username(self, username):
        existing_user = User.query.filter(User.username.ilike(username.data)).first()
        if existing_user:
            raise ValidationError('That username already exists. Please choosemessagedifferent one.')

class LoginForm(FlaskForm):
    """Form for user login"""
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('Remember Me')
    submit = SubmitField('continue')
 

# Authentication Routes
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration endpoint"""
    if current_user.is_authenticated:
        return redirect(url_for('messenger'))
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data
        # Hash password with PBKDF2 and salt
        password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=128)
        # Create AI chat for new user with encrypted welcome message
        ai_chat = Chat(name=username+"'s AI", messages='{"0": {"from": "'+username+'\'s AI", "message": "' + encrypt_text("Hello.") + '"}}', chat_type="AI", picture=os.getenv("AIPFP"))
        db.session.add(ai_chat)
        db.session.commit()
        # Create new user with reference to their AI chat
        new_user = User(username=username, password=password, chats=str(ai_chat.id))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'), success=True)
    return render_template('signup.html', form=form, error="Username already in use")

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login endpoint"""
    if current_user.is_authenticated:
        return redirect(url_for('messenger'))
    form = LoginForm()
    if form.validate_on_submit():
        # Case-insensitive username lookup
        user = User.query.filter(User.username.ilike(form.username.data)).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('messenger'))
        return render_template('login.html', form=form, error='Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """User logout endpoint"""
    logout_user()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    """Root route - redirects to messenger or login"""
    if current_user.is_authenticated:
        return redirect(url_for('messenger'))
    return redirect(url_for('login'))


@app.route('/messenger', methods=['GET'])
@login_required
def messenger():
    """Main messenger interface"""
    existing_chats_arr=[]
    # Get all chats the current user belongs to
    for chat in Chat.query.all():
        if chat.id in np.fromstring(current_user.chats, dtype=int, sep=","):
            chatname = chat.name
            # For group chats, remove current user's name from display
            if chat.chat_type!="AI": 
                chatnamearr = chatname.split(", ")
                for username in chatnamearr:
                    if username==current_user.username: chatnamearr.pop(chatnamearr.index(username))
                chatname = ", ".join(chatnamearr)
            existing_chats_arr.append([chatname, chat.messages, chat.picture, chat.id])
    # If specific chat is requested via URL parameter
    if request.args.get("chatid"):
        # Verify user has access to this chat
        if int(request.args.get("chatid")) not in np.fromstring(current_user.chats, dtype=int, sep=","):
            return redirect(url_for('messenger'))
        else:
            messages=[]
            try:
                # Decrypt and parse messages from selected chat
                for message in json.loads(Chat.query.filter_by(id=request.args.get("chatid")).first().messages).values():
                    try:
                        # Handle messages with images
                        messages.append([message['from'], decrypt_text(message['message']), message['image']])
                    except KeyError:
                        # Handle text-only messages
                        messages.append([message['from'], decrypt_text(message['message'])])
                # Move selected chat to top of chat list
                for ec in existing_chats_arr:
                    if str(ec[3])==str(request.args.get("chatid")):
                        existing_chats_arr.pop(existing_chats_arr.index(ec))
                        existing_chats_arr.insert(0, ec)
                return render_template('messenger.html', username=current_user.username, existing_chats=existing_chats_arr, message_history=messages, active_chat_id=request.args.get("chatid"))
            except AttributeError:
                return redirect(url_for("messenger"))
    return render_template('messenger.html', username=current_user.username, existing_chats=existing_chats_arr)
  

@app.route('/api', methods=['GET', 'POST'])
@login_required
def api():
    """API endpoint for various application functions"""
    if request.args.get("usersearch"):
         # User search functionality for creating new chats
        users={}
        for user in enumerate(User.query.filter(User.username.contains(request.args.get("usersearch"))).all()):
            # Exclude current user from search results
            if user[1].username!=current_user.username: users.update({user[0]: {"username": user[1].username, "picture": user[1].picture}})
        return users
    # Delete chat functionality
    if request.args.get("deletechat"):
        deletingchat = Chat.query.filter_by(id=request.args.get("deletechat")).first()
        # Prevent deletion of AI chats
        if deletingchat.chat_type=="AI":
            return redirect(url_for("messenger"))
        # Remove chat from all users who belong to it
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
    # Create new group chat
    if request.args.get("createchat"):
        userarr = []
        userarr.append(current_user.username)
         # Add selected users from request
        for i in json.loads(request.get_json())['users']:
            userarr.append(i)
        chatname = ", ".join(userarr)# Create chat name from usernames
        newchat = Chat(name=chatname, messages='{}', chat_type="GROUP", picture=os.getenv("DEFAULTPFP"))
        db.session.add(newchat)
        # Add chat ID to all participating users
        for user in userarr:
            currentchats=np.fromstring(User.query.filter_by(username=user).first().chats, dtype=int, sep=",").tolist()
            currentchats.append(newchat.id)
            User.query.filter_by(username=user).first().chats=','.join(map(str, currentchats))
        db.session.commit()
    # Get active user's username by session ID
    if request.args.get("username"):
        return User.query.filter_by(session_id=request.args.get("username")).first()
    return redirect(url_for("messenger"))

# SocketIO Event Handlers for Real-time Communication
@socketio.on('connect')
def handle_connection():
    """Handle new SocketIO connection"""
    # Store session ID for real-time messaging
    current_user.session_id=request.sid
    db.session.commit()
    # Join all chat rooms the user belongs to
    for chat in np.fromstring(current_user.chats, dtype=int, sep=",").tolist():
        join_room(str(chat))


@socketio.on('message')
def handle_message(message):
    """Handle incoming messages and AI responses"""
    # Determine sender (user or AI)
    sender = User.query.filter_by(session_id=json.loads(message)['sender']).first().username if json.loads(message)['sender']!="AI" else "AI"
    chat = Chat.query.filter_by(id=json.loads(message)['room']).first()
    
    # Broadcast message to all users in the chat room
    send(message, room=json.loads(message)['room'])

    # Store encrypted message in database
    messages = json.loads(chat.messages)
    messages.update({str(len(messages)): {"from": str(sender), "message": encrypt_text(json.loads(message)['message']), "image": str(json.loads(message).get('image', ''))}})
    chat.messages = json.dumps(messages)
    # Handle AI response for AI chats
    if chat.chat_type=="AI" and json.loads(message)['sender']!="AI":
        # Initialize Google Gemini AI client
        key = "AIzaSyDj1AltbH7wJ5-Wunwl1pxIFScWulWIrZg"
        client = genai.Client(api_key=key)
        input=json.loads(message)['message']
        # Handle image inputs for multimodal AI
        if json.loads(message).get('image', '')!='':
            # Decode base64 image
            decoded_image_bytes = base64.b64decode(json.loads(message).get('image', '').split(",")[1])
            image_stream = BytesIO(decoded_image_bytes)
            pil_image = Image.open(image_stream)
            input=[pil_image, json.loads(message)['message']]
        # Generate AI response with system instruction
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            config=types.GenerateContentConfig(
                system_instruction="When returning text/numbers, use already-formatted utf-8 charcters such as x² instead of x^2 etc.the user's username is {}".format(sender)),
            contents=input
            )
        # Send AI response back through the same message handle (RECURSION)
        aimessage = json.dumps({"message": str(response.text), "sender": "AI", "room": json.loads(message)["room"]})
        handle_message(aimessage)
    db.session.commit()


# Encryption/Decryption Functions for Message Security
def generate_key_from_password(password):
    """Generate Fernet-compatible key from password"""
    key = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(key)

def encrypt_text(text):
    """Encrypt text using application secret key"""
    password = os.getenv('SECRETKEY') #WOULD NOT BE HERE IF THIS WAS A REAL PRODUCT (the method would require a password input)
    key = generate_key_from_password(password)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(text.encode())
    return base64.urlsafe_b64encode(encrypted).decode()

def decrypt_text(encrypted_text):
    """Decrypt text using application secret key"""
    password = os.getenv('SECRETKEY') #WOULD NOT BE HERE IF THIS WAS A REAL PRODUCT (the method would require a password input)
    try:
        key = generate_key_from_password(password)
        fernet = Fernet(key)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        return f"Decryption failed: {e}"

# Application entry point
if __name__ == '__main__':
    socketio.run(app, debug=True)




