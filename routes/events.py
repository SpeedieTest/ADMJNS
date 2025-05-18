from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.event import Event, EventRegistration
from models.member import Member
from models.facility import Facility, Room
from datetime import datetime, timedelta
from app import db

events_routes = Blueprint('events', __name__, url_prefix='/events')

@events_routes.route('/')
@login_required
def index():
    # Get filter parameters
    view = request.args.get('view', 'upcoming')  # upcoming, past, all
    event_type = request.args.get('type')  # internal, external
    search = request.args.get('search')
    facility_id = request.args.get('facility_id')
    
    # Base query
    query = Event.query
    
    # Apply filters
    if view == 'upcoming':
        query = query.filter(Event.end_time >= datetime.now())
    elif view == 'past':
        query = query.filter(Event.end_time < datetime.now())
    
    if event_type == 'internal':
        query = query.filter_by(is_internal=True)
    elif event_type == 'external':
        query = query.filter_by(is_internal=False)
        
    if facility_id:
        query = query.filter_by(facility_id=facility_id)
    
    if search:
        query = query.filter(Event.name.ilike(f'%{search}%'))
    
    # Get events
    events = query.order_by(Event.start_time).all()
    
    # Get facilities for filter
    facilities = Facility.query.all()
    
    return render_template('events/index.html',
                         events=events,
                         view=view,
                         event_type=event_type,
                         search=search,
                         facilities=facilities,
                         selected_facility=facility_id)

@events_routes.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        try:
            is_internal = request.form.get('is_internal') == 'true'
            facility_id = request.form.get('facility_id') if is_internal else None
            room_id = request.form.get('room_id') if is_internal else None
            
            # Validate room availability if internal event
            if room_id:
                # Check for overlapping events in the same room
                start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
                end_time = datetime.strptime(request.form.get('end_time'), '%Y-%m-%dT%H:%M')
                
                overlapping = Event.query.filter(
                    Event.room_id == room_id,
                    Event.start_time < end_time,
                    Event.end_time > start_time,
                    Event.status != 'cancelled'
                ).first()
                
                if overlapping:
                    flash('This room is already booked during the selected time.', 'danger')
                    return redirect(url_for('events.create'))
            
            event = Event(
                name=request.form.get('name'),
                description=request.form.get('description'),
                start_time=datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M'),
                end_time=datetime.strptime(request.form.get('end_time'), '%Y-%m-%dT%H:%M'),
                location=request.form.get('location'),
                capacity=int(request.form.get('capacity') or 0),
                is_recurring=bool(request.form.get('is_recurring')),
                recurrence_pattern=request.form.get('recurrence_pattern'),
                recurrence_end_date=datetime.strptime(request.form.get('recurrence_end_date'), '%Y-%m-%d') if request.form.get('recurrence_end_date') else None,
                is_internal=is_internal,
                facility_id=facility_id,
                room_id=room_id
            )
            
            db.session.add(event)
            db.session.commit()
            
            flash('Event created successfully!', 'success')
            return redirect(url_for('events.view', id=event.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the event.', 'danger')
            return render_template('events/create.html')
    
    # Get facilities and rooms for form
    facilities = Facility.query.all()
    return render_template('events/create.html', facilities=facilities)

@events_routes.route('/get_rooms/<int:facility_id>')
@login_required
def get_rooms(facility_id):
    rooms = Room.query.filter_by(facility_id=facility_id).all()
    return jsonify([{'id': room.id, 'name': room.room_number} for room in rooms])

@events_routes.route('/view/<int:id>')
@login_required
def view(id):
    event = Event.query.get_or_404(id)
    registrations = EventRegistration.query.filter_by(event_id=id).all()
    
    # Check if current user (if member) is registered
    user_registration = None
    if hasattr(current_user, 'member'):
        user_registration = EventRegistration.query.filter_by(
            event_id=id,
            member_id=current_user.member.id
        ).first()
    
    # Calculate end date for recurring events
    now = datetime.now().date()
    end_date = None
    
    if event.is_recurring:
        if event.recurrence_end_date:
            end_date = event.recurrence_end_date.date()
        else:
            # Default to 3 months for unlimited recurring events
            end_date = now + timedelta(days=90)
    
    return render_template('events/view.html',
                         event=event,
                         registrations=registrations,
                         user_registration=user_registration,
                         now=now,
                         end_date=end_date,
                         timedelta=timedelta)

@events_routes.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    event = Event.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            is_internal = request.form.get('is_internal') == 'true'
            new_room_id = request.form.get('room_id') if is_internal else None
            
            # Check room availability if room is changing
            if new_room_id and new_room_id != str(event.room_id):
                start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
                end_time = datetime.strptime(request.form.get('end_time'), '%Y-%m-%dT%H:%M')
                
                overlapping = Event.query.filter(
                    Event.room_id == new_room_id,
                    Event.start_time < end_time,
                    Event.end_time > start_time,
                    Event.status != 'cancelled',
                    Event.id != event.id
                ).first()
                
                if overlapping:
                    flash('This room is already booked during the selected time.', 'danger')
                    return redirect(url_for('events.edit', id=event.id))
            
            event.name = request.form.get('name')
            event.description = request.form.get('description')
            event.start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
            event.end_time = datetime.strptime(request.form.get('end_time'), '%Y-%m-%dT%H:%M')
            event.location = request.form.get('location')
            event.capacity = int(request.form.get('capacity') or 0)
            event.is_recurring = bool(request.form.get('is_recurring'))
            event.recurrence_pattern = request.form.get('recurrence_pattern')
            event.recurrence_end_date = datetime.strptime(request.form.get('recurrence_end_date'), '%Y-%m-%d') if request.form.get('recurrence_end_date') else None
            event.is_internal = is_internal
            event.facility_id = request.form.get('facility_id') if is_internal else None
            event.room_id = new_room_id
            
            db.session.commit()
            flash('Event updated successfully!', 'success')
            return redirect(url_for('events.view', id=event.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the event.', 'danger')
    
    # Get facilities and rooms for form
    facilities = Facility.query.all()
    return render_template('events/edit.html', event=event, facilities=facilities)

@events_routes.route('/cancel/<int:id>', methods=['POST'])
@login_required
def cancel(id):
    if current_user.role not in ['admin', 'staff']:
        flash('You do not have permission to cancel events.', 'danger')
        return redirect(url_for('events.view', id=id))
    
    event = Event.query.get_or_404(id)
    
    try:
        event.cancel(current_user.id)
        db.session.commit()
        flash('Event cancelled successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while cancelling the event.', 'danger')
    
    return redirect(url_for('events.view', id=id))

@events_routes.route('/register/<int:id>', methods=['POST'])
@login_required
def register(id):
    event = Event.query.get_or_404(id)
    
    if event.is_full:
        flash('Sorry, this event is already at full capacity.', 'danger')
        return redirect(url_for('events.view', id=id))
    
    try:
        registration = EventRegistration(
            event_id=id,
            member_id=current_user.member.id,
            event_date=event.start_time,
            status='registered'
        )
        
        db.session.add(registration)
        db.session.commit()
        
        flash('Successfully registered for the event!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while registering for the event.', 'danger')
    
    return redirect(url_for('events.view', id=id))

@events_routes.route('/cancel-registration/<int:id>', methods=['POST'])
@login_required
def cancel_registration(id):
    registration = EventRegistration.query.get_or_404(id)
    
    if registration.member_id != current_user.member.id and current_user.role != 'admin':
        flash('You do not have permission to cancel this registration.', 'danger')
        return redirect(url_for('events.view', id=registration.event_id))
    
    try:
        registration.status = 'cancelled'
        db.session.commit()
        flash('Registration cancelled successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while cancelling the registration.', 'danger')
    
    return redirect(url_for('events.view', id=registration.event_id))

@events_routes.route('/mark-attendance/<int:id>', methods=['POST'])
@login_required
def mark_attendance(id):
    if current_user.role not in ['admin', 'staff']:
        flash('You do not have permission to mark attendance.', 'danger')
        return redirect(url_for('events.view', id=id))
    
    registration = EventRegistration.query.get_or_404(id)
    
    try:
        registration.status = 'attended'
        db.session.commit()
        flash('Attendance marked successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while marking attendance.', 'danger')
    
    return redirect(url_for('events.view', id=registration.event_id))

@events_routes.route('/cancel-occurrence/<int:id>/<date>', methods=['POST'])
@login_required
def cancel_occurrence(id, date):
    if current_user.role not in ['admin', 'staff']:
        flash('You do not have permission to cancel events.', 'danger')
        return redirect(url_for('events.view', id=id))
    
    event = Event.query.get_or_404(id)
    
    try:
        # Parse the date string
        cancel_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Find registrations for this occurrence
        registrations = EventRegistration.query.filter(
            EventRegistration.event_id == id,
            db.func.date(EventRegistration.event_date) == cancel_date
        ).all()
        
        # Cancel the registrations
        for registration in registrations:
            registration.status = 'cancelled'
        
        db.session.commit()
        flash('Event occurrence cancelled successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while cancelling the event occurrence.', 'danger')
    
    return redirect(url_for('events.view', id=id))