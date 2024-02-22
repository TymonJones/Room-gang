# 
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Room, Review

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://///.db'
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this!
db = SQLAlchemy(app)
jwt = JWTManager(app)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400
    user = User(username=username, password=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "User created"}), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Invalid username or password"}), 401

@app.route('/rooms', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    return jsonify([room.name for room in rooms]), 200

@app.route('/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    room = Room.query.get(room_id)
    if room:
        return jsonify(room.name), 200
    else:
        return jsonify({"msg": "Room not found"}), 404

@app.route('/rooms/<int:room_id>/book', methods=['POST'])
@jwt_required
def book_room(room_id):
    # Booking logic here
    return jsonify({"msg": "Room booked"}), 200

@app.route('/rooms/<int:room_id>/reviews', methods=['POST'])
@jwt_required
def leave_review(room_id):
    content = request.json.get('content', None)
    user_id = User.query.filter_by(username=get_jwt_identity()).first().id
    review = Review(content=content, user_id=user_id, room_id=room_id)
    db.session.add(review)
    db.session.commit()
    return jsonify({"msg": "Review left"}), 201

@app.route('/rooms/<int:room_id>/reviews/<int:review_id>', methods=['PUT', 'DELETE'])
@jwt_required
def update_or_delete_review(room_id, review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"msg": "Review not found"}), 404

    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    if review.user_id != current_user.id:
        return jsonify({"msg": "Permission denied"}), 403

    if request.method == 'PUT':
        content = request.json.get('content', None)
        if content:
            review.content = content
            db.session.commit()
            return jsonify({"msg": "Review updated"}), 200
        else:
            return jsonify({"msg": "No content provided"}), 400
    elif request.method == 'DELETE':
        db.session.delete(review)
        db.session.commit()
        return jsonify({"msg": "Review deleted"}), 200

if __name__ == '__main__':
    app.run(debug=True)
