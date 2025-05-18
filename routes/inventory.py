from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.inventory import InventoryItem, InventoryLog
from datetime import datetime
from app import db

inventory_routes = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_routes.route('/')
@login_required
def index():
    # Query parameters for filtering
    category = request.args.get('category')
    low_stock = request.args.get('low_stock')
    search = request.args.get('search')
    
    # Start with base query
    query = InventoryItem.query
    
    # Apply filters
    if category:
        query = query.filter_by(category=category)
    if low_stock:
        query = query.filter(InventoryItem.current_quantity <= InventoryItem.reorder_level)
    if search:
        query = query.filter(InventoryItem.name.ilike(f'%{search}%'))
    
    inventory_items = query.all()
    
    # Get unique categories for the filter dropdown
    categories = db.session.query(InventoryItem.category).distinct().all()
    categories = [c[0] for c in categories]
    
    return render_template('inventory/index.html', 
                          inventory_items=inventory_items,
                          categories=categories,
                          selected_category=category,
                          low_stock=low_stock,
                          search=search)

@inventory_routes.route('/view/<int:id>')
@login_required
def view(id):
    item = InventoryItem.query.get_or_404(id)
    logs = InventoryLog.query.filter_by(item_id=id).order_by(InventoryLog.date.desc()).all()
    
    return render_template('inventory/view.html', item=item, logs=logs)

@inventory_routes.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        description = request.form.get('description')
        unit = request.form.get('unit')
        current_quantity = float(request.form.get('current_quantity') or 0)
        minimum_quantity = float(request.form.get('minimum_quantity') or 0)
        reorder_level = float(request.form.get('reorder_level') or 0)
        cost_per_unit = float(request.form.get('cost_per_unit') or 0)
        supplier = request.form.get('supplier')
        supplier_contact = request.form.get('supplier_contact')
        location = request.form.get('location')
        
        # Additional medication fields
        pills_per_unit = None
        dosage_form = None
        strength = None
        manufacturer = None
        expiry_date = None
        
        if category == 'medical':
            pills_per_unit = int(request.form.get('pills_per_unit') or 0)
            dosage_form = request.form.get('dosage_form')
            strength = request.form.get('strength')
            manufacturer = request.form.get('manufacturer')
            expiry_date_str = request.form.get('expiry_date')
            if expiry_date_str:
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        
        item = InventoryItem(
            name=name,
            category=category,
            description=description,
            unit=unit,
            current_quantity=current_quantity,
            minimum_quantity=minimum_quantity,
            reorder_level=reorder_level,
            cost_per_unit=cost_per_unit,
            supplier=supplier,
            supplier_contact=supplier_contact,
            location=location,
            pills_per_unit=pills_per_unit,
            dosage_form=dosage_form,
            strength=strength,
            manufacturer=manufacturer,
            expiry_date=expiry_date
        )
        
        db.session.add(item)
        db.session.commit()
        
        # Create initial inventory log if starting with non-zero quantity
        if current_quantity > 0:
            log = InventoryLog(
                item_id=item.id,
                staff_id=current_user.id,
                log_type='received',
                quantity=current_quantity,
                previous_quantity=0,
                new_quantity=current_quantity,
                notes='Initial inventory'
            )
            db.session.add(log)
            db.session.commit()
        
        flash('Inventory item created successfully!', 'success')
        return redirect(url_for('inventory.view', id=item.id))
    
    return render_template('inventory/create.html')

@inventory_routes.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    item = InventoryItem.query.get_or_404(id)
    
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.category = request.form.get('category')
        item.description = request.form.get('description')
        item.unit = request.form.get('unit')
        item.minimum_quantity = float(request.form.get('minimum_quantity') or 0)
        item.reorder_level = float(request.form.get('reorder_level') or 0)
        item.cost_per_unit = float(request.form.get('cost_per_unit') or 0)
        item.supplier = request.form.get('supplier')
        item.supplier_contact = request.form.get('supplier_contact')
        item.location = request.form.get('location')
        
        # Update medication fields if category is medical
        if item.category == 'medical':
            item.pills_per_unit = int(request.form.get('pills_per_unit') or 0)
            item.dosage_form = request.form.get('dosage_form')
            item.strength = request.form.get('strength')
            item.manufacturer = request.form.get('manufacturer')
            expiry_date_str = request.form.get('expiry_date')
            if expiry_date_str:
                item.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        
        db.session.commit()
        flash('Inventory item updated successfully!', 'success')
        return redirect(url_for('inventory.view', id=item.id))
    
    return render_template('inventory/edit.html', item=item)

@inventory_routes.route('/add-log/<int:id>', methods=['GET', 'POST'])
@login_required
def add_log(id):
    item = InventoryItem.query.get_or_404(id)
    
    if request.method == 'POST':
        log_type = request.form.get('log_type')
        quantity = float(request.form.get('quantity') or 0)
        
        # Handle datetime-local input format (YYYY-MM-DDThh:mm)
        date_str = request.form.get('date')
        if date_str:
            try:
                # Replace 'T' with space to match our expected format
                date_str = date_str.replace('T', ' ')
                date = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
            except ValueError:
                date = datetime.now()
        else:
            date = datetime.now()
            
        notes = request.form.get('notes')
        
        previous_quantity = item.current_quantity
        
        # Update current quantity based on log type
        if log_type == 'received':
            item.current_quantity += quantity
            new_quantity = item.current_quantity
        elif log_type in ['used', 'expired', 'damaged']:
            if quantity > item.current_quantity:
                flash('Cannot reduce inventory by more than current quantity!', 'danger')
                return redirect(url_for('inventory.add_log', id=id))
            item.current_quantity -= quantity
            new_quantity = item.current_quantity
        else:
            # For adjustment or other log types
            new_quantity = previous_quantity
        
        log = InventoryLog(
            item_id=id,
            staff_id=current_user.id,
            log_type=log_type,
            quantity=quantity,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            date=date,
            notes=notes
        )
        
        db.session.add(log)
        db.session.commit()
        
        flash('Inventory log added successfully!', 'success')
        return redirect(url_for('inventory.view', id=id))
    
    return render_template('inventory/add_log.html', item=item)

@inventory_routes.route('/low-stock')
@login_required
def low_stock():
    items = InventoryItem.query.filter(
        InventoryItem.current_quantity <= InventoryItem.reorder_level
    ).all()
    
    return render_template('inventory/low_stock.html', items=items)

@inventory_routes.route('/reports')
@login_required
def reports():
    # Get query parameters for filtering
    report_type = request.args.get('report_type', 'usage')
    category = request.args.get('category')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Parse dates if provided
    if date_from:
        date_from = datetime.strptime(date_from, '%Y-%m-%d')
    else:
        date_from = datetime.now().replace(day=1)  # First day of current month
        
    if date_to:
        date_to = datetime.strptime(date_to, '%Y-%m-%d')
    else:
        date_to = datetime.now()
    
    # Start with base query
    query = InventoryLog.query.filter(
        InventoryLog.date >= date_from,
        InventoryLog.date <= date_to
    )
    
    # Filter by log type based on report type
    if report_type == 'usage':
        query = query.filter(InventoryLog.log_type == 'used')
    elif report_type == 'wastage':
        query = query.filter(InventoryLog.log_type.in_(['expired', 'damaged']))
    elif report_type == 'received':
        query = query.filter(InventoryLog.log_type == 'received')
    
    # If category filter is provided
    if category:
        # Need to join with InventoryItem to filter by category
        logs = db.session.query(InventoryLog).join(
            InventoryItem, InventoryLog.item_id == InventoryItem.id
        ).filter(
            InventoryItem.category == category,
            InventoryLog.date >= date_from,
            InventoryLog.date <= date_to
        )
        
        if report_type == 'usage':
            logs = logs.filter(InventoryLog.log_type == 'used')
        elif report_type == 'wastage':
            logs = logs.filter(InventoryLog.log_type.in_(['expired', 'damaged']))
        elif report_type == 'received':
            logs = logs.filter(InventoryLog.log_type == 'received')
            
        logs = logs.all()
    else:
        logs = query.all()
    
    # Get unique categories for the filter dropdown
    categories = db.session.query(InventoryItem.category).distinct().all()
    categories = [c[0] for c in categories]
    
    return render_template('inventory/reports.html',
                          logs=logs,
                          report_type=report_type,
                          categories=categories,
                          selected_category=category,
                          date_from=date_from,
                          date_to=date_to)