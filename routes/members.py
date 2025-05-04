# Start of the Members Routes
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models.member import Member, MedicalRecord, CareTask
from models.facility import Facility, Room
from datetime import datetime
import random
import string
from app import db

member_routes = Blueprint('members', __name__, url_prefix='/members')

def generate_member_id():
    prefix = "MEM"
    number = ''.join(random.choices(string.digits, k=6))
    year = datetime.now().strftime('%y')
    member_id = f"{prefix}-{number}-{year}"
    while Member.query.filter_by(medicare_number=member_id).first():
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
        db.session.commit()
        flash('Member updated successfully!', 'success')
        return redirect(url_for('members.view', id=member.id))
    facilities = Facility.query.all()
    rooms = Room.query.filter((Room.status == 'available') | (Room.id == member.room_id)).all()
    return render_template('members/edit.html', member=member, facilities=facilities, rooms=rooms)

@member_routes.route('/add-medical-record/<int:id>', methods=['GET', 'POST'])
@login_required
def add_medical_record(id):
    member = Member.query.get_or_404(id)
    if request.method == 'POST':
        record_type = request.form.get('record_type')
        description = request.form.get('description')
        record_date = datetime.strptime(request.form.get('record_date'), '%Y-%m-%d %H:%M') if request.form.get('record_date') else datetime.now()
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