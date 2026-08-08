from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'booking.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(200), nullable=True)

with app.app_context():
    db.create_all()

# ИМЕННО ЭТОТ МАРШРУТ ТЕПЕРЬ ПОКАЗЫВАЕТ САЙТ
@app.route('/')
def home():
    return render_template('index.html')

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