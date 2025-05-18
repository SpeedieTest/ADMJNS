from models import db
from datetime import datetime
import json

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
    room_type = db.Column(db.String(50), default='residential')  # residential, recreational, medical, storage, office
    floor = db.Column(db.String(10))
    capacity = db.Column(db.Integer, default=1)  # Seated capacity
    capacity_standing = db.Column(db.Integer)  # Standing capacity for events
    is_accessible = db.Column(db.Boolean, default=False)
    is_occupied = db.Column(db.Boolean, default=False)
    amenities = db.Column(db.Text)
    _features = db.Column('features', db.Text)  # Store as JSON string
    has_av_equipment = db.Column(db.Boolean, default=False)  # Audio/Visual equipment
    status = db.Column(db.String(20), default='available')  # available, occupied, maintenance, reserved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    residents = db.relationship('Member', backref='room', lazy=True)
    
    @property
    def features(self):
        """Get features list from JSON string"""
        if self._features:
            return json.loads(self._features)
        return []
        
    @features.setter
    def features(self, value):
        """Store features list as JSON string"""
        if value:
            self._features = json.dumps(value)
        else:
            self._features = None
    
    @property
    def is_recreational(self):
        return self.room_type == 'recreational'
    
    @property
    def total_capacity(self):
        """Returns standing capacity if available, otherwise seating capacity"""
        return self.capacity_standing or self.capacity
    
    @property
    def available_features(self):
        """Returns list of available features or empty list"""
        return self.features
    
    def __repr__(self):
        return f'<Room {self.room_number} at Facility {self.facility_id}>'