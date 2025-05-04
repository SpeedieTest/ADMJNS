from models import db
from datetime import datetime

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relation = db.Column(db.String(50))
    care_type = db.Column(db.String(20))  # in-home, residential
    admission_date = db.Column(db.Date)
    medicare_number = db.Column(db.String(20))
    health_insurance_provider = db.Column(db.String(100))
    health_insurance_number = db.Column(db.String(50))
    dietary_requirements = db.Column(db.Text)
    mobility_status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    medical_records = db.relationship('MedicalRecord', backref='member', lazy=True)
    care_tasks = db.relationship('CareTask', backref='member', lazy=True)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<Member {self.full_name}>'


class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    record_date = db.Column(db.DateTime, default=datetime.utcnow)
    record_type = db.Column(db.String(50))  # medication, assessment, incident
    description = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('staff.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MedicalRecord {self.id} for Member {self.member_id}>'


class CareTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    task_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    frequency = db.Column(db.String(50))  # daily, weekly, monthly, as needed
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    scheduled_time = db.Column(db.DateTime)
    completed_time = db.Column(db.DateTime)
    completed_by = db.Column(db.Integer, db.ForeignKey('staff.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CareTask {self.task_name} for Member {self.member_id}>'