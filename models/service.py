from models import db
from datetime import datetime

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # medical, personal care, housekeeping, social
    duration_minutes = db.Column(db.Integer)
    base_cost = db.Column(db.Float)
    requires_qualification = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    service_logs = db.relationship('ServiceLog', backref='service', lazy=True)
    
    def __repr__(self):
        return f'<Service {self.name}>'


class ServiceLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in-progress, completed, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    member = db.relationship('Member', backref='service_logs', lazy=True)
    staff = db.relationship('Staff', backref='service_logs', lazy=True)
    
    def __repr__(self):
        return f'<ServiceLog {self.id} for Service {self.service_id}>'