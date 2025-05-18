from models import db
from datetime import datetime

class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # medical, food, cleaning, equipment
    description = db.Column(db.Text)
    unit = db.Column(db.String(20))  # box, pack, item, kg
    current_quantity = db.Column(db.Float, default=0)
    minimum_quantity = db.Column(db.Float, default=0)
    reorder_level = db.Column(db.Float)
    cost_per_unit = db.Column(db.Float)
    supplier = db.Column(db.String(100))
    supplier_contact = db.Column(db.String(100))
    location = db.Column(db.String(100))
    
    # Medication specific fields
    pills_per_unit = db.Column(db.Integer)  # Number of pills per box/pack
    dosage_form = db.Column(db.String(50))  # tablet, capsule, liquid
    strength = db.Column(db.String(50))  # e.g., 500mg, 10ml
    manufacturer = db.Column(db.String(100))
    expiry_date = db.Column(db.Date)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inventory_logs = db.relationship('InventoryLog', backref='item', lazy=True)
    
    @property
    def total_pills(self):
        """Calculate total number of pills based on current quantity and pills per unit"""
        if self.category == 'medical' and self.pills_per_unit:
            return int(self.current_quantity * self.pills_per_unit)
        return None
    
    def __repr__(self):
        return f'<InventoryItem {self.name}>'


class InventoryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_item.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'))
    log_type = db.Column(db.String(20))  # received, used, expired, damaged
    quantity = db.Column(db.Float, nullable=False)
    previous_quantity = db.Column(db.Float)
    new_quantity = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<InventoryLog {self.id} for Item {self.item_id}>'