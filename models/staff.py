from models import db
from datetime import datetime

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    position = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    employee_id = db.Column(db.String(50), unique=True)
    employment_type = db.Column(db.String(50))  # full-time, part-time, casual, contractor
    employment_start_date = db.Column(db.Date)
    employment_end_date = db.Column(db.Date)
    hourly_rate = db.Column(db.Float)
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    qualifications = db.relationship('Qualification', backref='staff', lazy=True)
    schedules = db.relationship('Schedule', backref='staff', lazy=True, order_by='Schedule.start_time')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<Staff {self.full_name}>'


class Qualification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    qualification_name = db.Column(db.String(100), nullable=False)
    institution = db.Column(db.String(100))
    date_obtained = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    certificate_number = db.Column(db.String(50))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Qualification {self.qualification_name} for Staff {self.staff_id}>'