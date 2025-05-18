from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.facility import Facility, Room
from models.staff import Staff
from models.member import Member
from datetime import datetime
from app import db

facility_routes = Blueprint('facilities', __name__, url_prefix='/facilities')

@facility_routes.route('/')
@login_required
def index():
    facilities = Facility.query.all()
    return render_template('facilities/index.html', facilities=facilities)

@facility_routes.route('/view/<int:id>')
@login_required
def view(id):
    facility = Facility.query.get_or_404(id)
    rooms = Room.query.filter_by(facility_id=id).all()
    
    # Get occupancy statistics
    total_rooms = len(rooms)
    occupied_rooms = sum(1 for room in rooms if room.is_occupied)
    occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
    
    # Get residents in this facility
    residents = Member.query.filter_by(facility_id=id, is_active=True).all()
    
    return render_template('facilities/view.html', 
                          facility=facility, 
                          rooms=rooms, 
                          total_rooms=total_rooms,
                          occupied_rooms=occupied_rooms,
                          occupancy_rate=occupancy_rate,
                          residents=residents,
                          staff=Staff)

@facility_routes.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role != 'admin':
        flash('You do not have permission to create facilities.', 'danger')
        return redirect(url_for('facilities.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        phone = request.form.get('phone')
        email = request.form.get('email')
        capacity = request.form.get('capacity')
        manager_id = request.form.get('manager_id')
        
        # Validate required fields
        if not all([name, address, phone, email, capacity, manager_id]):
            flash('All fields are required.', 'danger')
            managers = Staff.query.filter_by(is_active=True).all()
            return render_template('facilities/create.html', managers=managers)
        
        try:
            facility = Facility(
                name=name,
                address=address,
                phone=phone,
                email=email,
                capacity=int(capacity),
                manager_id=int(manager_id),
                is_active=True
            )
            
            db.session.add(facility)
            db.session.commit()
            
            flash('Facility created successfully!', 'success')
            return redirect(url_for('facilities.view', id=facility.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the facility.', 'danger')
            managers = Staff.query.filter_by(is_active=True).all()
            return render_template('facilities/create.html', managers=managers)
    
    managers = Staff.query.filter_by(is_active=True).all()
    return render_template('facilities/create.html', managers=managers)

@facility_routes.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role != 'admin':
        flash('You do not have permission to edit facilities.', 'danger')
        return redirect(url_for('facilities.index'))
    
    facility = Facility.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            facility.name = request.form.get('name')
            facility.address = request.form.get('address')
            facility.phone = request.form.get('phone')
            facility.email = request.form.get('email')
            facility.capacity = int(request.form.get('capacity'))
            facility.manager_id = int(request.form.get('manager_id'))
            facility.is_active = True if request.form.get('is_active') else False
            
            db.session.commit()
            flash('Facility updated successfully!', 'success')
            return redirect(url_for('facilities.view', id=facility.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the facility.', 'danger')
    
    managers = Staff.query.filter_by(is_active=True).all()
    return render_template('facilities/edit.html', facility=facility, managers=managers)

@facility_routes.route('/add-room/<int:facility_id>', methods=['GET', 'POST'])
@login_required
def add_room(facility_id):
    facility = Facility.query.get_or_404(facility_id)
    
    if request.method == 'POST':
        try:
            room_number = request.form.get('room_number')
            room_type = request.form.get('room_type')
            floor = request.form.get('floor')
            capacity = request.form.get('capacity')
            is_accessible = True if request.form.get('is_accessible') else False
            amenities = request.form.get('amenities')
            
            # Check if room number already exists in this facility
            existing_room = Room.query.filter_by(facility_id=facility_id, room_number=room_number).first()
            if existing_room:
                flash('A room with this number already exists in this facility.', 'danger')
                return redirect(url_for('facilities.add_room', facility_id=facility_id))
            
            room = Room(
                facility_id=facility_id,
                room_number=room_number,
                room_type=room_type,
                floor=floor,
                capacity=int(capacity),
                is_accessible=is_accessible,
                amenities=amenities,
                status='available'
            )
            
            db.session.add(room)
            db.session.commit()
            
            flash('Room added successfully!', 'success')
            return redirect(url_for('facilities.view', id=facility_id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the room.', 'danger')
    
    return render_template('facilities/add_room.html', facility=facility)

@facility_routes.route('/edit-room/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_room(id):
    room = Room.query.get_or_404(id)
    facility = Facility.query.get(room.facility_id)
    
    if request.method == 'POST':
        try:
            room.room_number = request.form.get('room_number')
            room.room_type = request.form.get('room_type')
            room.floor = request.form.get('floor')
            room.capacity = int(request.form.get('capacity'))
            room.is_accessible = True if request.form.get('is_accessible') else False
            room.amenities = request.form.get('amenities')
            new_status = request.form.get('status')
            
            # Handle status changes
            if new_status != room.status:
                room.status = new_status
                if new_status == 'maintenance':
                    # If room is under maintenance and was occupied, handle residents
                    if room.is_occupied:
                        for resident in room.residents:
                            resident.room_id = None
                        room.is_occupied = False
                elif new_status == 'available':
                    room.is_occupied = False
            
            db.session.commit()
            flash('Room updated successfully!', 'success')
            return redirect(url_for('facilities.view', id=room.facility_id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the room.', 'danger')
    
    return render_template('facilities/edit_room.html', room=room, facility=facility)

@facility_routes.route('/view-room/<int:id>')
@login_required
def view_room(id):
    room = Room.query.get_or_404(id)
    facility = Facility.query.get(room.facility_id)
    residents = Member.query.filter_by(room_id=id).all()
    
    return render_template('facilities/view_room.html', room=room, facility=facility, residents=residents)