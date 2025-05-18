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
    assigned_residents = db.relationship('Member', secondary='schedule_residents', 
                                       backref=db.backref('schedules', lazy=True))
    staff = db.relationship('Staff', back_populates='schedules', foreign_keys=[staff_id])

# Association table for schedule-resident many-to-many relationship
schedule_residents = db.Table('schedule_residents',
    db.Column('schedule_id', db.Integer, db.ForeignKey('schedule.id'), primary_key=True),
    db.Column('member_id', db.Integer, db.ForeignKey('member.id'), primary_key=True)
)