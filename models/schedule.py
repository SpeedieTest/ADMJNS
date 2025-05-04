from models import db
from datetime import datetime

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    schedule_type = db.Column(db.String(20))  # regular, overtime, on-call
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in-progress, completed, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    service_logs = db.relationship('ServiceLog', backref='schedule', lazy=True)
    
    def __repr__(self):
        return f'<Schedule {self.id} for Staff {self.staff_id}>'