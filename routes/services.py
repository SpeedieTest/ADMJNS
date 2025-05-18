from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.service import Service, ServiceLog
from models.member import Member
from models.staff import Staff
from models.schedule import Schedule
from datetime import datetime, timedelta
from app import db

service_routes = Blueprint('services', __name__, url_prefix='/services')

@service_routes.route('/')
@login_required
def index():
    # Get query parameters for filtering
    category = request.args.get('category')
    search = request.args.get('search')
    show_inactive = request.args.get('show_inactive') == '1'
    
    # Start with base query
    query = Service.query
    
    # Apply filters
    if category:
        query = query.filter_by(category=category)
    if search:
        search_term = f"%{search}%"
        query = query.filter(Service.name.ilike(search_term))
    if not show_inactive:
        query = query.filter_by(is_active=True)
    
    # Get unique categories for filter dropdown
    categories = db.session.query(Service.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    services = query.order_by(Service.name).all()
    
    return render_template('services/index.html',
                         services=services,
                         categories=categories,
                         selected_category=category,
                         search=search,
                         show_inactive=show_inactive)

@service_routes.route('/view/<int:id>')
@login_required
def view(id):
    service = Service.query.get_or_404(id)
    
    # Get recent service logs
    recent_logs = ServiceLog.query.filter_by(service_id=id)\
        .order_by(ServiceLog.start_time.desc())\
        .limit(10)\
        .all()
    
    # Get upcoming scheduled services
    upcoming_services = ServiceLog.query.filter_by(
        service_id=id,
        status='scheduled'
    ).filter(
        ServiceLog.start_time >= datetime.now()
    ).order_by(
        ServiceLog.start_time
    ).limit(5).all()
    
    return render_template('services/view.html',
                         service=service,
                         recent_logs=recent_logs,
                         upcoming_services=upcoming_services)

@service_routes.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role != 'admin':
        flash('You do not have permission to create services.', 'danger')
        return redirect(url_for('services.index'))
    
    if request.method == 'POST':
        try:
            service = Service(
                name=request.form.get('name'),
                description=request.form.get('description'),
                category=request.form.get('category'),
                duration_minutes=int(request.form.get('duration_minutes') or 0),
                base_cost=float(request.form.get('base_cost') or 0),
                requires_qualification=request.form.get('requires_qualification'),
                is_active=True
            )
            
            db.session.add(service)
            db.session.commit()
            
            flash('Service created successfully!', 'success')
            return redirect(url_for('services.view', id=service.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the service.', 'danger')
            return render_template('services/create.html')
    
    return render_template('services/create.html')

@service_routes.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role != 'admin':
        flash('You do not have permission to edit services.', 'danger')
        return redirect(url_for('services.index'))
    
    service = Service.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            service.name = request.form.get('name')
            service.description = request.form.get('description')
            service.category = request.form.get('category')
            service.duration_minutes = int(request.form.get('duration_minutes') or 0)
            service.base_cost = float(request.form.get('base_cost') or 0)
            service.requires_qualification = request.form.get('requires_qualification')
            service.is_active = request.form.get('is_active') == 'on'
            
            db.session.commit()
            flash('Service updated successfully!', 'success')
            return redirect(url_for('services.view', id=service.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the service.', 'danger')
    
    return render_template('services/edit.html', service=service)

@service_routes.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    if request.method == 'POST':
        try:
            service_id = request.form.get('service_id')
            member_id = request.form.get('member_id')
            staff_id = request.form.get('staff_id')
            schedule_id = request.form.get('schedule_id')
            start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
            
            # Get service duration
            service = Service.query.get(service_id)
            duration = service.duration_minutes or 60  # Default to 60 minutes
            end_time = start_time + timedelta(minutes=duration)
            
            # Create service log
            service_log = ServiceLog(
                service_id=service_id,
                member_id=member_id,
                staff_id=staff_id,
                schedule_id=schedule_id,
                start_time=start_time,
                end_time=end_time,
                status='scheduled'
            )
            
            db.session.add(service_log)
            db.session.commit()
            
            flash('Service scheduled successfully!', 'success')
            return redirect(url_for('services.view_log', id=service_log.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while scheduling the service.', 'danger')
    
    # Get data for dropdowns
    services = Service.query.filter_by(is_active=True).order_by(Service.name).all()
    members = Member.query.filter_by(is_active=True).order_by(Member.first_name).all()
    staff = Staff.query.filter_by(is_active=True).order_by(Staff.first_name).all()
    
    # Get schedule if provided
    schedule = None
    schedule_id = request.args.get('schedule_id')
    if schedule_id:
        schedule = Schedule.query.get(schedule_id)
    
    return render_template('services/schedule.html',
                         services=services,
                         members=members,
                         staff=staff,
                         schedule=schedule)

@service_routes.route('/view-log/<int:id>')
@login_required
def view_log(id):
    log = ServiceLog.query.get_or_404(id)
    return render_template('services/view_log.html', log=log)

@service_routes.route('/update-log-status/<int:id>', methods=['POST'])
@login_required
def update_log_status(id):
    log = ServiceLog.query.get_or_404(id)
    
    if log.staff_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to update this service log.', 'danger')
        return redirect(url_for('services.view_log', id=id))
    
    try:
        new_status = request.form.get('status')
        
        # Handle completion
        if new_status == 'completed' and log.status != 'completed':
            log.end_time = datetime.now()
        
        log.status = new_status
        log.notes = request.form.get('notes')
        
        db.session.commit()
        flash('Service log updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating the service log.', 'danger')
    
    return redirect(url_for('services.view_log', id=id))

@service_routes.route('/logs')
@login_required
def logs():
    # Get filter parameters
    status = request.args.get('status')
    member_id = request.args.get('member_id')
    staff_id = request.args.get('staff_id')
    service_id = request.args.get('service_id')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Start with base query
    query = ServiceLog.query
    
    # Apply filters
    if status:
        query = query.filter_by(status=status)
    if member_id:
        query = query.filter_by(member_id=member_id)
    if staff_id:
        query = query.filter_by(staff_id=staff_id)
    if service_id:
        query = query.filter_by(service_id=service_id)
    if date_from:
        date_from = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(ServiceLog.start_time >= date_from)
    if date_to:
        date_to = datetime.strptime(date_to, '%Y-%m-%d')
        query = query.filter(ServiceLog.start_time <= date_to)
    
    # Get ordered results
    logs = query.order_by(ServiceLog.start_time.desc()).all()
    
    # Get filter options
    services = Service.query.order_by(Service.name).all()
    members = Member.query.filter_by(is_active=True).order_by(Member.first_name).all()
    staff_members = Staff.query.filter_by(is_active=True).order_by(Staff.first_name).all()
    
    return render_template('services/logs.html',
                         logs=logs,
                         services=services,
                         members=members,
                         staff_members=staff_members,
                         selected_status=status,
                         selected_member=member_id,
                         selected_staff=staff_id,
                         selected_service=service_id,
                         date_from=date_from,
                         date_to=date_to)