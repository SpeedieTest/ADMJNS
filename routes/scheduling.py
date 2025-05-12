from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.schedule import Schedule
from models.staff import Staff
from models.service import ServiceLog
from models.member import Member
from forms import ScheduleForm, ScheduleEditForm, BulkScheduleForm
from datetime import datetime, timedelta
from app import db

scheduling_routes = Blueprint('scheduling', __name__, url_prefix='/scheduling')

scheduling_routes = Blueprint('scheduling', __name__, url_prefix='/scheduling')

@scheduling_routes.route('/')
@login_required
def index():
    # Get date range for calendar view
    start_date = request.args.get('start_date')
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        # Default to current week
        today = datetime.now().date()
        start_date = today - timedelta(days=today.weekday())  # Monday of current week
    
    end_date = start_date + timedelta(days=6)  # Show a week at a time
    
    # Get all schedules in the date range
    schedules = Schedule.query.filter(
        Schedule.start_time >= datetime.combine(start_date, datetime.min.time()),
        Schedule.end_time <= datetime.combine(end_date, datetime.max.time())
    ).order_by(Schedule.start_time).all()
    
    # Get all staff for filtering
    staff_members = Staff.query.filter_by(is_active=True).all()
    
    # Filter by staff if requested
    staff_id = request.args.get('staff_id')
    if staff_id:
        schedules = [s for s in schedules if str(s.staff_id) == staff_id]
    
    return render_template('scheduling/index.html', 
                          schedules=schedules, 
                          staff_members=staff_members,
                          start_date=start_date,
                          end_date=end_date,
                          selected_staff_id=staff_id,
                          timedelta=timedelta,
                          Staff=Staff)

@scheduling_routes.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = ScheduleForm()
    
    if form.validate_on_submit():
        start_datetime = datetime.combine(form.start_date.data, form.start_time.data)
        end_datetime = datetime.combine(form.end_date.data, form.end_time.data)
        
        # Check for overlapping schedules
        overlapping = Schedule.query.filter(
            Schedule.staff_id == form.staff_id.data,
            Schedule.start_time < end_datetime,
            Schedule.end_time > start_datetime
        ).first()
        
        if overlapping:
            flash('This schedule overlaps with an existing schedule for this staff member.', 'danger')
            return render_template('scheduling/create.html', form=form)
        
        try:
            schedule = Schedule(
                staff_id=form.staff_id.data,
                start_time=start_datetime,
                end_time=end_datetime,
                schedule_type=form.schedule_type.data,
                notes=form.notes.data
            )
            
            db.session.add(schedule)
            db.session.commit()
            
            flash('Schedule created successfully! You can now assign residents.', 'success')
            return redirect(url_for('scheduling.edit', id=schedule.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the schedule.', 'danger')
            return render_template('scheduling/create.html', form=form)
    
    return render_template('scheduling/create.html', form=form, Staff=Staff)

@scheduling_routes.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    schedule = Schedule.query.get_or_404(id)
    form = ScheduleEditForm(obj=schedule)
    
    if form.validate_on_submit():
        try:
            start_datetime = datetime.combine(form.start_date.data, form.start_time.data)
            end_datetime = datetime.combine(form.end_date.data, form.end_time.data)
            
            # Check for overlapping schedules (excluding this one)
            overlapping = Schedule.query.filter(
                Schedule.id != id,
                Schedule.staff_id == form.staff_id.data,
                Schedule.start_time < end_datetime,
                Schedule.end_time > start_datetime
            ).first()
            
            if overlapping:
                flash('This schedule overlaps with an existing schedule for this staff member.', 'danger')
                return render_template('scheduling/edit.html', form=form, schedule=schedule)
            
            schedule.staff_id = form.staff_id.data
            schedule.start_time = start_datetime
            schedule.end_time = end_datetime
            schedule.schedule_type = form.schedule_type.data
            schedule.notes = form.notes.data
            
            # Update assigned residents
            schedule.assigned_residents = []
            if form.assigned_residents.data:
                residents = Member.query.filter(Member.id.in_(form.assigned_residents.data)).all()
                schedule.assigned_residents.extend(residents)
            
            db.session.commit()
            flash('Schedule updated successfully!', 'success')
            return redirect(url_for('scheduling.view', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the schedule.', 'danger')
    
    # Pre-fill the form with existing data
    if not form.is_submitted():
        form.start_date.data = schedule.start_time.date()
        form.start_time.data = schedule.start_time.time()
        form.end_date.data = schedule.end_time.date()
        form.end_time.data = schedule.end_time.time()
        form.assigned_residents.data = [r.id for r in schedule.assigned_residents]
    
    return render_template('scheduling/edit.html', form=form, schedule=schedule, Staff=Staff)

@scheduling_routes.route('/view/<int:id>')
@login_required
def view(id):
    schedule = Schedule.query.get_or_404(id)
    staff = Staff.query.get(schedule.staff_id)
    
    # Get services scheduled during this time
    services = ServiceLog.query.filter_by(
        staff_id=schedule.staff_id,
        schedule_id=schedule.id
    ).all()
    
    return render_template('scheduling/view.html', 
                          schedule=schedule, 
                          staff=staff,
                          services=services,
                          Staff=Staff)

@scheduling_routes.route('/cancel/<int:id>', methods=['POST'])
@login_required
def cancel(id):
    schedule = Schedule.query.get_or_404(id)
    
    try:
        # Check if services are linked to this schedule
        services = ServiceLog.query.filter_by(schedule_id=id).all()
        if services:
            for service in services:
                service.status = 'cancelled'
        
        schedule.status = 'cancelled'
        db.session.commit()
        
        flash('Schedule cancelled successfully.', 'success')
        return redirect(url_for('scheduling.index'))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while cancelling the schedule.', 'danger')
        return redirect(url_for('scheduling.view', id=id))

@scheduling_routes.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    schedule = Schedule.query.get_or_404(id)
    
    try:
        # Delete any associated service logs
        ServiceLog.query.filter_by(schedule_id=id).delete()
        
        # Delete the schedule
        db.session.delete(schedule)
        db.session.commit()
        
        flash('Schedule deleted successfully.', 'success')
        return redirect(url_for('scheduling.index'))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the schedule.', 'danger')
        return redirect(url_for('scheduling.view', id=id))

@scheduling_routes.route('/staff-availability')
@login_required
def staff_availability():
    date = request.args.get('date')
    if date:
        date = datetime.strptime(date, '%Y-%m-%d').date()
    else:
        date = datetime.now().date()
    
    # Get schedules for all staff on this date
    day_start = datetime.combine(date, datetime.min.time())
    day_end = datetime.combine(date, datetime.max.time())
    
    # Get all active staff
    staff_members = Staff.query.filter_by(is_active=True).all()
    
    availability = []
    for staff in staff_members:
        # Get schedules for this staff member on this date
        schedules = Schedule.query.filter(
            Schedule.staff_id == staff.id,
            Schedule.start_time < day_end,
            Schedule.end_time > day_start,
            Schedule.status != 'cancelled'
        ).all()
        
        # Calculate available hours
        hours_scheduled = sum((min(s.end_time, day_end) - max(s.start_time, day_start)).total_seconds() / 3600 for s in schedules)
        hours_available = 24 - hours_scheduled
        
        availability.append({
            'staff_id': staff.id,
            'name': staff.full_name,
            'position': staff.position,
            'hours_scheduled': hours_scheduled,
            'hours_available': hours_available,
            'schedules': schedules
        })
    
    return render_template('scheduling/availability.html',
                          availability=availability,
                          date=date,
                          Staff=Staff)

@scheduling_routes.route('/bulk-create', methods=['GET', 'POST'])
@login_required
def bulk_create():
    form = BulkScheduleForm()
    
    if form.validate_on_submit():
        try:
            created_count = 0
            skipped_count = 0
            
            current_date = form.start_date.data
            while current_date <= form.end_date.data:
                # Check if this day of the week is selected
                if current_date.weekday() in form.days.data:
                    # For each staff member
                    for staff_id in form.staff_ids.data:
                        # Create the schedule datetime objects
                        schedule_start = datetime.combine(current_date, form.start_time.data)
                        schedule_end = datetime.combine(current_date, form.end_time.data)
                        
                        # Check for overlapping schedules
                        overlapping = Schedule.query.filter(
                            Schedule.staff_id == staff_id,
                            Schedule.start_time < schedule_end,
                            Schedule.end_time > schedule_start
                        ).first()
                        
                        if not overlapping:
                            schedule = Schedule(
                                staff_id=staff_id,
                                start_time=schedule_start,
                                end_time=schedule_end,
                                schedule_type=form.schedule_type.data,
                                notes=f"Bulk created on {datetime.now().strftime('%Y-%m-%d')}"
                            )
                            db.session.add(schedule)
                            created_count += 1
                        else:
                            skipped_count += 1
                
                # Move to next day
                current_date += timedelta(days=1)
            
            db.session.commit()
            
            if created_count > 0:
                flash(f'Successfully created {created_count} schedules. Skipped {skipped_count} due to overlaps.', 'success')
            else:
                flash(f'No schedules were created. {skipped_count} were skipped due to overlaps.', 'warning')
                
            return redirect(url_for('scheduling.index'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the schedules.', 'danger')
    
    return render_template('scheduling/bulk_create.html', form=form, Staff=Staff)