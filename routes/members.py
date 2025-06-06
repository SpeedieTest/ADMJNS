from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.member import Member, MedicalRecord, CareTask
from models.facility import Facility, Room
from datetime import datetime
import random
import string
from app import db

member_routes = Blueprint('members', __name__, url_prefix='/members')

def generate_member_id():
    # Generate a prefix for member ID (MEM)
    prefix = "MEM"
    
    # Generate a random 6-digit number
    number = ''.join(random.choices(string.digits, k=6))
    
    # Get current year (last 2 digits)
    year = datetime.now().strftime('%y')
    
    # Combine to create member ID: MEM-RANDOM-YY
    member_id = f"{prefix}-{number}-{year}"
    
    # Check if ID already exists, if so, generate a new one
    while Member.query.filter_by(id=member_id).first():
        number = ''.join(random.choices(string.digits, k=6))
        member_id = f"{prefix}-{number}-{year}"
    
    return member_id

@member_routes.route('/')
@login_required
def index():
    members = Member.query.all()
    return render_template('members/index.html', members=members)

@member_routes.route('/view/<int:id>')
@login_required
def view(id):
    member = Member.query.get_or_404(id)
    medical_records = MedicalRecord.query.filter_by(member_id=id).order_by(MedicalRecord.record_date.desc()).all()
    care_tasks = CareTask.query.filter_by(member_id=id).order_by(CareTask.scheduled_time.desc()).all()
    return render_template('members/view.html', member=member, medical_records=medical_records, care_tasks=care_tasks)

@member_routes.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        try:
            # Generate member ID
            medicare_number = generate_member_id()
            
            member = Member(
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d'),
                gender=request.form.get('gender'),
                address=request.form.get('address'),
                phone=request.form.get('phone'),
                email=request.form.get('email'),
                emergency_contact_name=request.form.get('emergency_contact_name'),
                emergency_contact_phone=request.form.get('emergency_contact_phone'),
                emergency_contact_relation=request.form.get('emergency_contact_relation'),
                care_type=request.form.get('care_type'),
                admission_date=datetime.strptime(request.form.get('admission_date'), '%Y-%m-%d') if request.form.get('admission_date') else None,
                medicare_number=medicare_number,
                health_insurance_provider=request.form.get('health_insurance_provider'),
                health_insurance_number=request.form.get('health_insurance_number'),
                dietary_requirements=request.form.get('dietary_requirements'),
                mobility_status=request.form.get('mobility_status'),
                facility_id=request.form.get('facility_id'),
                room_id=request.form.get('room_id')
            )
            
            db.session.add(member)
            db.session.commit()
            
            flash('Member created successfully!', 'success')
            return redirect(url_for('members.view', id=member.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the member.', 'danger')
            facilities = Facility.query.all()
            rooms = Room.query.filter_by(status='available').all()
            return render_template('members/create.html', facilities=facilities, rooms=rooms)
    
    facilities = Facility.query.all()
    rooms = Room.query.filter_by(status='available').all()
    return render_template('members/create.html', facilities=facilities, rooms=rooms)

@member_routes.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    member = Member.query.get_or_404(id)
    
    if request.method == 'POST':
        member.first_name = request.form.get('first_name')
        member.last_name = request.form.get('last_name')
        member.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d')
        member.gender = request.form.get('gender')
        member.address = request.form.get('address')
        member.phone = request.form.get('phone')
        member.email = request.form.get('email')
        member.emergency_contact_name = request.form.get('emergency_contact_name')
        member.emergency_contact_phone = request.form.get('emergency_contact_phone')
        member.emergency_contact_relation = request.form.get('emergency_contact_relation')
        member.care_type = request.form.get('care_type')
        member.admission_date = datetime.strptime(request.form.get('admission_date'), '%Y-%m-%d') if request.form.get('admission_date') else None
        member.medicare_number = request.form.get('medicare_number')
        member.health_insurance_provider = request.form.get('health_insurance_provider')
        member.health_insurance_number = request.form.get('health_insurance_number')
        member.dietary_requirements = request.form.get('dietary_requirements')
        member.mobility_status = request.form.get('mobility_status')
        
        # Handle facility and room changes carefully
        new_facility_id = request.form.get('facility_id')
        new_room_id = request.form.get('room_id')
        
        if new_facility_id and new_facility_id != str(member.facility_id):
            member.facility_id = new_facility_id
        
        if new_room_id and new_room_id != str(member.room_id):
            # Update old room status if exists
            if member.room_id:
                old_room = Room.query.get(member.room_id)
                if old_room:
                    old_room.status = 'available'
                    old_room.is_occupied = False
            
            # Update new room status
            new_room = Room.query.get(new_room_id)
            if new_room:
                new_room.status = 'occupied'
                new_room.is_occupied = True
            
            member.room_id = new_room_id
            
        db.session.commit()
        flash('Member updated successfully!', 'success')
        return redirect(url_for('members.view', id=member.id))
    
    facilities = Facility.query.all()
    
    # For rooms, include both available rooms and the member's current room
    rooms = Room.query.filter(
        (Room.status == 'available') | (Room.id == member.room_id)
    ).all()
    
    return render_template('members/edit.html', member=member, facilities=facilities, rooms=rooms)

@member_routes.route('/add-medical-record/<int:id>', methods=['GET', 'POST'])
@login_required
def add_medical_record(id):
    member = Member.query.get_or_404(id)
    
    if request.method == 'POST':
        record_type = request.form.get('record_type')
        description = request.form.get('description')
        record_date_str = request.form.get('record_date')
        
        # Handle datetime-local input format (YYYY-MM-DDThh:mm)
        if record_date_str:
            try:
                record_date = datetime.strptime(record_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                record_date = datetime.now()
        else:
            record_date = datetime.now()
        
        medical_record = MedicalRecord(
            member_id=id,
            record_type=record_type,
            description=description,
            record_date=record_date,
            recorded_by=current_user.id
        )
        
        db.session.add(medical_record)
        db.session.commit()
        
        flash('Medical record added successfully!', 'success')
        return redirect(url_for('members.view', id=id))
    
    return render_template('members/add_medical_record.html', member=member)

@member_routes.route('/add-care-task/<int:id>', methods=['GET', 'POST'])
@login_required
def add_care_task(id):
    member = Member.query.get_or_404(id)
    
    if request.method == 'POST':
        task_name = request.form.get('task_name')
        description = request.form.get('description')
        frequency = request.form.get('frequency')
        scheduled_time_str = request.form.get('scheduled_time')
        
        # Handle the datetime-local input format
        scheduled_time = None
        if scheduled_time_str:
            try:
                # Convert from HTML datetime-local format (YYYY-MM-DDTHH:MM) to datetime object
                scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Invalid date format. Please use the date picker.', 'danger')
                return render_template('members/add_care_task.html', member=member)
        
        care_task = CareTask(
            member_id=id,
            task_name=task_name,
            description=description,
            frequency=frequency,
            scheduled_time=scheduled_time
        )
        
        db.session.add(care_task)
        db.session.commit()
        
        flash('Care task added successfully!', 'success')
        return redirect(url_for('members.view', id=id))
    
    return render_template('members/add_care_task.html', member=member)

@member_routes.route('/complete-care-task/<int:task_id>', methods=['POST'])
@login_required
def complete_care_task(task_id):
    care_task = CareTask.query.get_or_404(task_id)
    care_task.status = 'completed'
    care_task.completed_time = datetime.now()
    care_task.completed_by = current_user.id
    
    db.session.commit()
    flash('Care task marked as completed!', 'success')
    return redirect(url_for('members.view', id=care_task.member_id))