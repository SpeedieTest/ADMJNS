# Start of the Sceduling Routes
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.schedule import Schedule
from models.staff import Staff
from datetime import datetime, timedelta
from app import db

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