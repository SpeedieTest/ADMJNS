from models import db
from datetime import datetime

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    capacity = db.Column(db.Integer)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.String(50))  # daily, weekly, monthly
    recurrence_end_date = db.Column(db.DateTime)
    is_internal = db.Column(db.Boolean, default=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    status = db.Column(db.String(20), default='active')  # active, cancelled
    cancelled_at = db.Column(db.DateTime)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('staff.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    registrations = db.relationship('EventRegistration', backref='event', lazy=True)
    facility = db.relationship('Facility', backref=db.backref('events', lazy=True))
    cancelled_by_staff = db.relationship('Staff', backref='cancelled_events', lazy=True)
    event_room = db.relationship('Room', backref=db.backref('hosted_events', lazy=True))
    
    @property
    def registered_count(self):
        return len([r for r in self.registrations if r.status == 'registered'])
    
    @property
    def is_full(self):
        return self.capacity and self.registered_count >= self.capacity
    
    @property
    def is_cancelled(self):
        return self.status == 'cancelled'
    
    def cancel(self, staff_id):
        """Cancel the event but preserve past occurrences if recurring"""
        self.status = 'cancelled'
        self.cancelled_at = datetime.utcnow()
        self.cancelled_by = staff_id
        
        # For recurring events, only cancel future registrations
        if self.is_recurring:
            now = datetime.utcnow()
            for registration in self.registrations:
                if registration.event_date > now:
                    registration.status = 'cancelled'
    
    def __repr__(self):
        return f'<Event {self.name}>'


class EventRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    event_date = db.Column(db.DateTime, nullable=False)  # Specific date for recurring events
    status = db.Column(db.String(20), default='registered')  # registered, cancelled, attended
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<EventRegistration {self.id} for Event {self.event_id}>'