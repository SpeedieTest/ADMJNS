from flask_wtf import FlaskForm
from wtforms import (EmailField, PasswordField, StringField, SelectField, 
                     DateField, TextAreaField, DecimalField, BooleanField, TimeField)
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
from models.user import User
from models.staff import Staff

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
        
