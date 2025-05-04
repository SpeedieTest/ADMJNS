from models import db
from datetime import datetime

class Facility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    capacity = db.Column(db.Integer)
    manager_id = db.Column(db.Integer, db.ForeignKey('staff.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rooms = db.relationship('Room', backref='facility', lazy=True)
    members = db.relationship('Member', backref='facility', lazy=True)
    
    def __repr__(self):
        return f'<Facility {self.name}>'


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'), nullable=False)
    room_number = db.Column(db.String(10), nullable=False)
    room_type = db.Column(db.String(50))  # single, shared, suite
    floor = db.Column(db.String(10))
    capacity = db.Column(db.Integer, default=1)
    is_accessible = db.Column(db.Boolean, default=False)
    is_occupied = db.Column(db.Boolean, default=False)
    amenities = db.Column(db.Text)
    status = db.Column(db.String(20), default='available')  # available, occupied, maintenance, reserved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    residents = db.relationship('Member', backref='room', lazy=True)
    
    def __repr__(self):
        return f'<Room {self.room_number} at Facility {self.facility_id}>'