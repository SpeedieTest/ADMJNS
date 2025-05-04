# Start of the Members Routes
from flask import Blueprint, render_template
from flask_login import login_required
from models.member import Member, MedicalRecord, CareTask

member_routes = Blueprint('members', __name__, url_prefix='/members')

@member_routes.route('/')
@login_required
def index():
    members = Member.query.all()
    return render_template('members/index.html', members=members)

@member_routes.route('/view/<int:id>')
@login_required
def view(id):
    member = Member.query.get_or_404(id)
    medical_records = MedicalRecord.query.filter_by(member_id=id).order_by(MedicalRecord.record_date.desc()).all()
    care_tasks = CareTask.query.filter_by(member_id=id).order_by(CareTask.scheduled_time.desc()).all()
    return render_template('members/view.html', member=member, medical_records=medical_records, care_tasks=care_tasks)