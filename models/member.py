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
    emergency_contact_email = db.Column(db.String(100))  # Added for emergency contact login
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
    
    # User account associations
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # For resident login
    emergency_contact_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # For emergency contact login
    
    # Relationships
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    medical_records = db.relationship('MedicalRecord', backref='member', lazy=True)
    care_tasks = db.relationship('CareTask', backref='member', lazy=True)
    event_registrations = db.relationship('EventRegistration', backref='member', lazy=True)
    user = db.relationship('User', foreign_keys=[user_id], backref='member_account', lazy=True)
    emergency_contact_user = db.relationship('User', foreign_keys=[emergency_contact_user_id], backref='emergency_contact_for', lazy=True)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def current_carer(self):
        """Get the current carer assigned to this member"""
        from models.schedule import Schedule
        from models.staff import Staff
        from datetime import datetime
        
        current_schedule = Schedule.query.join(Staff).filter(
            Schedule.status != 'cancelled',
            Schedule.start_time <= datetime.now(),
            Schedule.end_time >= datetime.now(),
            Schedule.assigned_residents.any(id=self.id)
        ).first()
        
        return current_schedule.staff if current_schedule else None
    
    @property
    def upcoming_appointments(self):
        """Get upcoming service appointments"""
        from models.service import ServiceLog
        from datetime import datetime
        
        return ServiceLog.query.filter(
            ServiceLog.member_id == self.id,
            ServiceLog.start_time >= datetime.now(),
            ServiceLog.status == 'scheduled'
        ).order_by(ServiceLog.start_time).all()
    
    @property
    def upcoming_events(self):
        """Get upcoming events the member is registered for"""
        from models.event import EventRegistration, Event
        from datetime import datetime
        
        return EventRegistration.query.join(Event).filter(
            EventRegistration.member_id == self.id,
            EventRegistration.status == 'registered',
            Event.start_time >= datetime.now()
        ).order_by(Event.start_time).all()
    
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