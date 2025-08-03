# MessageApplication
This is a real-time messaging application built with Flask, SocketIO, and Google Gemini AI. Features encrypted messaging, group chats, image sharing, and intelligent AI responses.
## 🚀 Features
### Messaging
- Real-time Communication: Instant messaging using WebSocket connections
- Group Chats: Create group conversations
- Image Sharing: Upload and share images with base64 encoding

### Security
- Message Encryption: All messages encrypted using Fernet symmetric encryption
- User Authentication: Secure login/signup with password hashing

### AI Integration
- Personal AI Assistant: Each user gets their own AI chat powered by Google Gemini (Currently doesnt have contextual capabilities)
- Multimodal Support: AI can process both text and images

### User Interface
- Modern Dark Theme: Sleek monospace design with blue/purple accents
- Responsive Layout: CSS Grid-based layout that adapts to screen size
- Smooth Animations: Hover effects and transitions throughout
- Intuitive UX: Click-to-navigate, keyboard shortcuts, and visual feedback

## 🛠️ Tech Stack
### Backend
- Flask - Python web framework
- Flask-SocketIO - Real-time WebSocket communication
- SQLAlchemy - Database ORM
- Flask-Login - User session management
- WTForms - Form handling and validation
- Cryptography - Message encryption (Fernet)
- Google Gemini AI - AI chat responses
- PIL (Pillow) - Image processing

### Frontend
- Vanilla JavaScript - Client-side functionality
- Socket.IO Client - Real-time communication
- CSS Grid - Modern layout system
- Material Icons - Google's icon font
- Custom CSS - Dark theme with animations

### Database
SQLAlchemy - Lightweight ORM database

## 📦 Installation
### Prerequisites
- Python 3.8+
- pip package manager

### Setup Steps
1. Clone/Download the repository
2. Install Dependencies
```bash
pip install flask flask-sqlalchemy flask-login flask-wtf flask-socketio
pip install wtforms werkzeug cryptography python-dotenv
pip install google-generativeai pillow numpy
```
3. Run the application!
```bash
python app.py
```

## 🔧 Configuration
### Environment Variables
- SECRETKEY Flask secret key for sessions and encryption
- DEFAULTPFP Default profile picture (Base64 Encoded)
- AIPFPAI chat profile picture (Base64 Encoded)
### Google AI Setup
1. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Replace the hardcoded API key in app.py line 205 with your key
3. Important: Move the API key to environment variables for production

## 📱 Usage
### Getting Started
- Sign Up: Create a new account with username and password
- Login: Access your account
- AI Chat: Start chatting with your personal AI assistant
- Create Groups: Click the group icon to create group chats
- Send Messages: Type messages and press Enter to send
- Share Images: Click the photo icon to upload and share images

### Keyboard Shortcuts
- Enter: Send message
- Shift + Enter: New line in message
- Tab: Navigate through interface elements

### Chat Management
- Delete Chats: Hover over chat and click delete icon (confirmation required)
- Switch Chats: Click on any chat in the sidebar
- Real-time Updates: Messages appear instantly across all connected clients

## Database Schema
### Users Table
- id: Primary key
- username: Unique username
- password: Hashed password
- chats: Comma-separated chat IDs
- picture: Profile picture URL
- session_id: SocketIO session ID
### Chats Table
- id: Primary key
- name: Chat name (comma-separated usernames for groups)
- picture: Chat profile picture
- messages: JSON string of encrypted messages
- chat_type: "AI" or "GROUP"
