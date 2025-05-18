from flask import Flask, render_template, redirect, url_for
from models import db
from flask_login import LoginManager, current_user
from datetime import datetime
import os

# Initialize extensions
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aged_care.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['WTF_CSRF_ENABLED'] = True
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    #THIS ONE
    # Import blueprints
    from routes.auth import auth_routes
    from routes.dashboard import dashboard_routes
    from routes.members import member_routes
    from routes.staff import staff_routes
    from routes.services import service_routes
    from routes.facilities import facility_routes
    from routes.scheduling import scheduling_routes
    from routes.inventory import inventory_routes
    from routes.events import events_routes
    
    # Register blueprints
    app.register_blueprint(auth_routes)
    app.register_blueprint(dashboard_routes)
    app.register_blueprint(member_routes)
    app.register_blueprint(staff_routes)
    app.register_blueprint(service_routes)
    app.register_blueprint(facility_routes)
    app.register_blueprint(scheduling_routes)
    app.register_blueprint(inventory_routes)
    app.register_blueprint(events_routes)
    
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role in ['staff', 'admin']:
                return redirect(url_for('dashboard.index'))
            else:
                return redirect(url_for('dashboard.member'))
        return render_template('index.html')
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}

    with app.app_context():
        # Import models
        from models.user import User
        from models.member import Member, MedicalRecord, CareTask
        from models.staff import Staff, Qualification
        from models.service import Service, ServiceLog
        from models.facility import Facility, Room
        from models.schedule import Schedule
        from models.inventory import InventoryItem, InventoryLog
        from models.event import Event, EventRegistration
        
        # Create tables
        db.create_all()
        
        # Create admin user if not exists
        admin = User.query.filter_by(email='admin@agedcare.com').first()
        if not admin:
            admin = User(
                name='Administrator',
                email='admin@agedcare.com',
                password='admin123',
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)