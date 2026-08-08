from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sunway-secret-key-123' 

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'booking.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- DATABASE MODELS ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(200), nullable=True)
    # NEW: Link the room to the user who booked it
    booked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- WEB PAGES (ROUTES) ---

@app.route('/')
def home():
    return render_template('index.html', current_user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
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
        confirm_password = request.form.get('confirm_password')
        
        if not re.match("^[a-zA-Z0-9_]+$", username):
            return render_template('register.html', error="Username can only contain English letters, numbers, and underscores.")

        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match!")
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            return render_template('register.html', error="Username already exists!")
            
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
            "image_url": room.image_url,
            # NEW: Tell the frontend if the logged-in user owns this booking
            "is_my_booking": True if current_user.is_authenticated and room.booked_by == current_user.id else False
        })
    return jsonify(rooms_list)

@app.route('/book/<int:room_id>', methods=['POST'])
@login_required 
def book_room(room_id):
    room = Room.query.get(room_id)
    if room and not room.is_booked:
        room.is_booked = True
        room.booked_by = current_user.id # Assign user ID to room
        db.session.commit()
        return jsonify({"message": f"Success! {room.title} is now booked."}), 200
    return jsonify({"error": "Room not found or already booked."}), 400

# NEW ROUTE: Cancel a booking
@app.route('/unbook/<int:room_id>', methods=['POST'])
@login_required
def unbook_room(room_id):
    room = Room.query.get(room_id)
    if room and room.is_booked:
        # Verify that the person cancelling is the person who booked it
        if room.booked_by == current_user.id:
            room.is_booked = False
            room.booked_by = None
            db.session.commit()
            return jsonify({"message": f"Success! Booking for {room.title} has been cancelled."}), 200
        else:
            return jsonify({"error": "Permission denied. You can only cancel your own bookings."}), 403
    return jsonify({"error": "Room not found or not booked."}), 400

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