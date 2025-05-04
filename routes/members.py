# Start of the Members Routes
from flask import Blueprint, render_template
from flask_login import login_required
from models.member import Member

member_routes = Blueprint('members', __name__, url_prefix='/members')

@member_routes.route('/')
@login_required
def index():
    members = Member.query.all()
    return render_template('members/index.html', members=members)