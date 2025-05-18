from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models.user import User
from models.member import Member
from models.staff import Staff
from forms import MemberLoginForm, MemberRegistrationForm, EmergencyContactRegistrationForm
from app import db
from datetime import datetime

auth_routes = Blueprint('auth', __name__)

@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role in ['staff', 'admin']:
            return redirect(url_for('dashboard.index'))
        else:
            return redirect(url_for('dashboard.member'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        login_as = request.form.get('login_as')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.verify_password(password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('This account has been deactivated. Please contact an administrator.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Verify user type matches login form
        if login_as == 'staff' and user.role not in ['staff', 'admin']:
            flash('Invalid login type. Please use member login.', 'danger')
            return redirect(url_for('auth.login'))
        elif login_as == 'member' and user.role not in ['member', 'emergency_contact']:
            flash('Invalid login type. Please use staff login.', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=remember)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            if user.role in ['staff', 'admin']:
                next_page = url_for('dashboard.index')
            else:
                next_page = url_for('dashboard.member')
            
        flash('Logged in successfully!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html')

@auth_routes.route('/register/member', methods=['GET', 'POST'])
def register_member():
    form = MemberRegistrationForm()
    
    if form.validate_on_submit():
        member = Member.query.filter_by(id=form.member_id.data).first()
        
        if not member:
            flash('Invalid Member ID.', 'danger')
            return render_template('auth/register_member.html', form=form)
        
        user = User(
            name=member.full_name,
            email=form.email.data,
            role='member'
        )
        user.password = form.password.data
        
        db.session.add(user)
        member.user_id = user.id
        db.session.commit()
        
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register_member.html', form=form)

@auth_routes.route('/register/emergency-contact', methods=['GET', 'POST'])
def register_emergency_contact():
    form = EmergencyContactRegistrationForm()
    
    if form.validate_on_submit():
        member = Member.query.filter_by(id=form.member_id.data).first()
        
        if not member:
            flash('Invalid Member ID.', 'danger')
            return render_template('auth/register_emergency_contact.html', form=form)
        
        if member.emergency_contact_phone != form.contact_phone.data:
            flash('Phone number does not match emergency contact on file.', 'danger')
            return render_template('auth/register_emergency_contact.html', form=form)
        
        user = User(
            name=member.emergency_contact_name,
            email=form.email.data,
            role='emergency_contact'
        )
        user.password = form.password.data
        
        db.session.add(user)
        member.emergency_contact_user_id = user.id
        member.emergency_contact_email = form.email.data
        db.session.commit()
        
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register_emergency_contact.html', form=form)

@auth_routes.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_routes.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')

@auth_routes.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.verify_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        current_user.password = new_password
        db.session.commit()
        flash('Your password has been updated.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')