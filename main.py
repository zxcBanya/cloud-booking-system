from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
# Secret key is required by Flask to secure user sessions
app.config['SECRET_KEY'] = 'sunway-secret-key-123' 

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'booking.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- DATABASE MODELS ---

# 1. User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

# 2. Room Model
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(200), nullable=True)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- WEB PAGES (ROUTES) ---

@app.route('/')
def home():
    # Pass current_user to HTML to change UI based on login status
    return render_template('index.html', current_user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password matches the hash
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid username or password")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if username is already taken
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            return render_template('register.html', error="Username already exists")
            
        # Hash the password for security
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- API ENDPOINTS ---

@app.route('/rooms', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    rooms_list = []
    for room in rooms:
        rooms_list.append({
            "id": room.id,
            "title": room.title,
            "price": room.price,
            "is_booked": room.is_booked,
            "image_url": room.image_url
        })
    return jsonify(rooms_list)

@app.route('/book/<int:room_id>', methods=['POST'])
@login_required # ONLY LOGGED IN USERS CAN ACCESS THIS
def book_room(room_id):
    room = Room.query.get(room_id)
    if room and not room.is_booked:
        room.is_booked = True
        db.session.commit()
        return jsonify({"message": f"Success! {room.title} is now booked."}), 200
    return jsonify({"error": "Room not found or already booked."}), 400

@app.route('/seed', methods=['GET'])
def seed_data():
    if Room.query.count() == 0:
        room1 = Room(title="Master Bedroom at Sunway Geo Residences", price=1200.0, is_booked=False)
        room2 = Room(title="Cozy Single Room near Sunway University", price=850.0, is_booked=False)
        room3 = Room(title="Studio Apartment walking distance to Sunway Pyramid", price=1800.0, is_booked=False)
        
        db.session.add(room1)
        db.session.add(room2)
        db.session.add(room3)
        db.session.commit()
        return {"message": "Sunway test rooms added to the database!"}
    
    return {"message": "Database already contains data."}

if __name__ == '__main__':
    app.run(debug=True)