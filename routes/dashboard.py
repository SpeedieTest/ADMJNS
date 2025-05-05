from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.member import Member
from models.staff import Staff
from models.service import ServiceLog
from models.inventory import InventoryItem
from datetime import datetime, timedelta

dashboard_routes = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_routes.route('/')
@login_required
def index():
    # Quick stats for dashboard
    total_members = Member.query.filter_by(is_active=True).count()
    total_staff = Staff.query.filter_by(is_active=True).count()
    
    # Services scheduled for today
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    today_services = ServiceLog.query.filter(
        ServiceLog.start_time >= today_start,
        ServiceLog.start_time <= today_end
    ).count()
    
    # Inventory items below reorder level
    low_inventory = InventoryItem.query.filter(
        InventoryItem.current_quantity <= InventoryItem.reorder_level
    ).count()
    
    # Get upcoming services for quick view
    upcoming_services = ServiceLog.query.filter(
        ServiceLog.start_time >= datetime.now(),
        ServiceLog.start_time <= datetime.now() + timedelta(days=7),
        ServiceLog.status.in_(['scheduled', 'in-progress'])
    ).order_by(ServiceLog.start_time.asc()).limit(5).all()
    
    return render_template('dashboard/index.html', 
                           total_members=total_members,
                           total_staff=total_staff,
                           today_services=today_services,
                           low_inventory=low_inventory,
                           upcoming_services=upcoming_services)

@dashboard_routes.route('/analytics')
@login_required
def analytics():
    # This would contain more detailed analytics and reporting
    return render_template('dashboard/analytics.html')