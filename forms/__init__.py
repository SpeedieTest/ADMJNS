from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField, SelectField, 
                    DateField, TimeField, TextAreaField, DecimalField, 
                    EmailField, SelectMultipleField)
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
from models.staff import Staff
from models.user import User
from models.member import Member

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

class StaffForm(FlaskForm):
    # Account Information
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[('staff', 'Staff'), ('admin', 'Administrator')], validators=[DataRequired()])
    
    # Personal Information
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    gender = SelectField('Gender', choices=[('', 'Select Gender'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    
    # Contact Information
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    
    # Employment Information
    position = StringField('Position', validators=[DataRequired(), Length(max=100)])
    department = SelectField('Department', choices=[
        ('', 'Select Department'),
        ('nursing', 'Nursing'),
        ('medical', 'Medical'),
        ('therapy', 'Therapy'),
        ('support', 'Support'),
        ('administration', 'Administration')
    ], validators=[DataRequired()])
    employment_type = SelectField('Employment Type', choices=[
        ('', 'Select Type'),
        ('full-time', 'Full Time'),
        ('part-time', 'Part Time'),
        ('casual', 'Casual'),
        ('contractor', 'Contractor')
    ], validators=[DataRequired()])
    employment_start_date = DateField('Start Date', validators=[DataRequired()])
    hourly_rate = DecimalField('Hourly Rate', validators=[DataRequired()])
    
    # Emergency Contact
    emergency_contact_name = StringField('Emergency Contact Name', validators=[DataRequired()])
    emergency_contact_phone = StringField('Emergency Contact Phone', validators=[DataRequired()])
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

class StaffEditForm(FlaskForm):
    # Account Information
    role = SelectField('Role', choices=[('staff', 'Staff'), ('admin', 'Administrator')], validators=[DataRequired()])
    
    # Personal Information
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    gender = SelectField('Gender', choices=[('', 'Select Gender'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    
    # Contact Information
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    
    # Employment Information
    position = StringField('Position', validators=[DataRequired(), Length(max=100)])
    department = SelectField('Department', choices=[
        ('', 'Select Department'),
        ('nursing', 'Nursing'),
        ('medical', 'Medical'),
        ('therapy', 'Therapy'),
        ('support', 'Support'),
        ('administration', 'Administration')
    ], validators=[DataRequired()])
    employment_type = SelectField('Employment Type', choices=[
        ('', 'Select Type'),
        ('full-time', 'Full Time'),
        ('part-time', 'Part Time'),
        ('casual', 'Casual'),
        ('contractor', 'Contractor')
    ], validators=[DataRequired()])
    employment_start_date = DateField('Start Date', validators=[DataRequired()])
    hourly_rate = DecimalField('Hourly Rate', validators=[DataRequired()])
    
    # Emergency Contact
    emergency_contact_name = StringField('Emergency Contact Name', validators=[DataRequired()])
    emergency_contact_phone = StringField('Emergency Contact Phone', validators=[DataRequired()])

# This is the start of the Flask Form validation
class ScheduleForm(FlaskForm):
    staff_id = SelectField('Staff Member', coerce=int, validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])
    schedule_type = SelectField('Schedule Type', choices=[
        ('regular', 'Regular Shift'),
        ('overtime', 'Overtime'),
        ('on-call', 'On Call')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(ScheduleForm, self).__init__(*args, **kwargs)
        self.staff_id.choices = [(s.id, f"{s.full_name} ({s.position})") for s in Staff.query.filter_by(is_active=True).all()]

class ScheduleEditForm(FlaskForm):
    staff_id = SelectField('Staff Member', coerce=int, validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])
    schedule_type = SelectField('Schedule Type', choices=[
        ('regular', 'Regular Shift'),
        ('overtime', 'Overtime'),
        ('on-call', 'On Call')
    ], validators=[DataRequired()])
    assigned_residents = SelectMultipleField('Assigned Residents', coerce=int)
    notes = TextAreaField('Notes', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(ScheduleEditForm, self).__init__(*args, **kwargs)
        # Only show Carer staff for resident assignments
        self.staff_id.choices = [(s.id, f"{s.full_name} ({s.position})") for s in Staff.query.filter_by(is_active=True).all()]
        # Only allow resident assignments for Carer staff
        staff_id = kwargs.get('obj', None)
        if staff_id:
            staff = Staff.query.get(staff_id.staff_id)
            if staff and staff.position.lower() == 'carer':
                self.assigned_residents.choices = [(m.id, f"{m.full_name} ({m.care_type})") for m in Member.query.filter_by(is_active=True).all()]
            else:
                self.assigned_residents.choices = []

    def validate_assigned_residents(self, field):
        if not field.data:
            return
            
        # Check if staff is a Carer
        staff = Staff.query.get(self.staff_id.data)
        if not staff or staff.position.lower() != 'carer':
            raise ValidationError('Only Carers can be assigned residents')
            
        residents = Member.query.filter(Member.id.in_(field.data)).all()
        residential_count = sum(1 for r in residents if r.care_type == 'residential')
        inhome_count = sum(1 for r in residents if r.care_type == 'in-home')
        
        if residential_count > 5:
            raise ValidationError('Cannot assign more than 5 residential care patients to a shift')
        if inhome_count > 2:
            raise ValidationError('Cannot assign more than 2 in-home care patients to a shift')

class BulkScheduleForm(FlaskForm):
    staff_ids = SelectMultipleField('Staff Members', coerce=int, validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    days = SelectMultipleField('Days', coerce=int, choices=[
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ], validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])
    schedule_type = SelectField('Schedule Type', choices=[
        ('regular', 'Regular Shift'),
        ('overtime', 'Overtime'),
        ('on-call', 'On Call')
    ], validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super(BulkScheduleForm, self).__init__(*args, **kwargs)
        self.staff_ids.choices = [(s.id, f"{s.full_name} ({s.position})") for s in Staff.query.filter_by(is_active=True).all()]
        
