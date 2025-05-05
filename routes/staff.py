from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.staff import Staff, Qualification
from models.user import User
from models.schedule import Schedule
from forms import StaffForm, StaffEditForm
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from sqlalchemy import or_
from app import db
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

staff_routes = Blueprint('staff', __name__, url_prefix='/staff')

@staff_routes.route('/')
@login_required
def index():
    # Get search parameters
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()
    position = request.args.get('position', '').strip()
    
    # Start with base query
    query = Staff.query
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Staff.first_name.ilike(search_term),
                Staff.last_name.ilike(search_term),
                Staff.email.ilike(search_term),
                Staff.employee_id.ilike(search_term)
            )
        )
    
    # Apply department filter if provided
    if department:
        query = query.filter(Staff.department == department)
    
    # Apply position filter if provided
    if position:
        query = query.filter(Staff.position == position)
    
    # Get unique departments and positions for filter dropdowns
    departments = db.session.query(Staff.department).distinct().all()
    positions = db.session.query(Staff.position).distinct().all()
    
    # Execute query and get results
    staff_members = query.all()
    
    return render_template('staff/index.html', 
                         staff_members=staff_members,
                         departments=[d[0] for d in departments if d[0]],
                         positions=[p[0] for p in positions if p[0]],
                         search=search,
                         selected_department=department,
                         selected_position=position)

@staff_routes.route('/view/<int:id>')
@login_required
def view(id):
    staff = Staff.query.get_or_404(id)
    qualifications = Qualification.query.filter_by(staff_id=id).all()
    user = User.query.get(staff.user_id)
    
    # Calculate annual salary for full-time and part-time staff
    annual_salary = None
    if staff.employment_type in ['full-time', 'part-time']:
        weekly_hours = 38 if staff.employment_type == 'full-time' else 20
        annual_salary = staff.hourly_rate * weekly_hours * 52
    
    # Get current date for calendar
    today = datetime.now().date()
    
    # Get start of week (Monday)
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=6)
    
    # Get schedules for the current week
    schedules = Schedule.query.filter(
        Schedule.staff_id == id,
        Schedule.start_time >= datetime.combine(start_date, datetime.min.time()),
        Schedule.end_time <= datetime.combine(end_date, datetime.max.time()),
        Schedule.status != 'cancelled'
    ).order_by(Schedule.start_time).all()
    
    return render_template('staff/view.html',
                         staff=staff,
                         qualifications=qualifications,
                         user=user,
                         annual_salary=annual_salary,
                         today=today,
                         start_date=start_date,
                         end_date=end_date,
                         schedules=schedules,
                         timedelta=timedelta)

@staff_routes.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role != 'admin':
        flash('You do not have permission to create staff members.', 'danger')
        return redirect(url_for('staff.index'))
    
    form = StaffForm()
    logger.debug("Form created")
    
    if form.validate_on_submit():
        logger.debug("Form validated")
        try:
            # Create user account
            logger.debug(f"Creating user with email: {form.email.data}")
            user = User(
                name=f"{form.first_name.data} {form.last_name.data}",
                email=form.email.data,
                role=form.role.data
            )
            user.password = form.password.data  # This will use the password setter to hash
            logger.debug("User object created")
            
            db.session.add(user)
            db.session.commit()  # Commit to get the user.id
            logger.debug(f"User created with ID: {user.id}")
            
            # Generate employee ID based on department
            employee_id = f"{form.department.data[:2].upper()}-{datetime.now().strftime('%y%m%d')}-{user.id:04d}"
            logger.debug(f"Generated employee ID: {employee_id}")
            
            # Create staff profile
            logger.debug("Creating staff profile")
            staff = Staff(
                user_id=user.id,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                date_of_birth=form.date_of_birth.data,
                gender=form.gender.data,
                address=form.address.data,
                phone=form.phone.data,
                email=form.email.data,
                position=form.position.data,
                department=form.department.data,
                employee_id=employee_id,
                employment_type=form.employment_type.data,
                employment_start_date=form.employment_start_date.data,
                hourly_rate=form.hourly_rate.data,
                emergency_contact_name=form.emergency_contact_name.data,
                emergency_contact_phone=form.emergency_contact_phone.data,
                is_active=True
            )
            logger.debug("Staff object created")
            
            db.session.add(staff)
            db.session.commit()
            logger.debug(f"Staff profile created with ID: {staff.id}")
            
            flash('Staff member created successfully!', 'success')
            return redirect(url_for('staff.view', id=staff.id))
            
        except Exception as e:
            logger.error(f"Error creating staff member: {str(e)}")
            db.session.rollback()
            flash('An error occurred while creating the staff member.', 'danger')
            return render_template('staff/create.html', form=form)
    else:
        if form.errors:
            logger.debug(f"Form validation errors: {form.errors}")
    
    return render_template('staff/create.html', form=form)

@staff_routes.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role != 'admin':
        flash('You do not have permission to edit staff members.', 'danger')
        return redirect(url_for('staff.index'))
    
    staff = Staff.query.get_or_404(id)
    user = User.query.get(staff.user_id)
    form = StaffEditForm(obj=staff)
    
    if form.validate_on_submit():
        try:
            logger.debug("Form validated, updating staff member")
            
            # Update user information
            user.role = form.role.data
            user.name = f"{form.first_name.data} {form.last_name.data}"
            
            # Update staff information
            staff.first_name = form.first_name.data
            staff.last_name = form.last_name.data
            staff.date_of_birth = form.date_of_birth.data
            staff.gender = form.gender.data
            staff.address = form.address.data
            staff.phone = form.phone.data
            staff.position = form.position.data
            staff.department = form.department.data
            staff.employment_type = form.employment_type.data
            staff.employment_start_date = form.employment_start_date.data
            staff.hourly_rate = form.hourly_rate.data
            staff.emergency_contact_name = form.emergency_contact_name.data
            staff.emergency_contact_phone = form.emergency_contact_phone.data
            
            logger.debug("Committing changes to database")
            db.session.commit()
            
            flash('Staff member updated successfully!', 'success')
            return redirect(url_for('staff.view', id=staff.id))
            
        except Exception as e:
            logger.error(f"Error updating staff member: {str(e)}")
            db.session.rollback()
            flash('An error occurred while updating the staff member.', 'danger')
    else:
        if form.errors:
            logger.debug(f"Form validation errors: {form.errors}")
    
    # Pre-fill form with existing data
    if not form.is_submitted():
        form.role.data = user.role
    
    return render_template('staff/edit.html', form=form, staff=staff, user=user)

@staff_routes.route('/add-qualification/<int:staff_id>', methods=['GET', 'POST'])
@login_required
def add_qualification(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    
    if request.method == 'POST':
        try:
            qualification = Qualification(
                staff_id=staff_id,
                qualification_name=request.form.get('qualification_name'),
                institution=request.form.get('institution'),
                date_obtained=datetime.strptime(request.form.get('date_obtained'), '%Y-%m-%d') if request.form.get('date_obtained') else None,
                expiry_date=datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d') if request.form.get('expiry_date') else None,
                certificate_number=request.form.get('certificate_number'),
                description=request.form.get('description')
            )
            
            db.session.add(qualification)
            db.session.commit()
            
            flash('Qualification added successfully!', 'success')
            return redirect(url_for('staff.view', id=staff_id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the qualification.', 'danger')
    
    return render_template('staff/add_qualification.html', staff=staff)

@staff_routes.route('/deactivate/<int:id>', methods=['POST'])
@login_required
def deactivate(id):
    if current_user.role != 'admin':
        flash('You do not have permission to deactivate staff members.', 'danger')
        return redirect(url_for('staff.index'))
    
    staff = Staff.query.get_or_404(id)
    user = User.query.get(staff.user_id)
    
    staff.is_active = False
    user.is_active = False
    db.session.commit()
    
    flash('Staff member deactivated successfully.', 'success')
    return redirect(url_for('staff.index'))

@staff_routes.route('/activate/<int:id>', methods=['POST'])
@login_required
def activate(id):
    if current_user.role != 'admin':
        flash('You do not have permission to activate staff members.', 'danger')
        return redirect(url_for('staff.index'))
    
    staff = Staff.query.get_or_404(id)
    user = User.query.get(staff.user_id)
    
    staff.is_active = True
    user.is_active = True
    db.session.commit()
    
    flash('Staff member activated successfully.', 'success')
    return redirect(url_for('staff.index'))