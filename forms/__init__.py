# This is the start of the Flask Form validation
class ScheduleForm(FlaskForm):
    staff_id = SelectField('Staff Member', coerce=int, validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])
    schedule_type = SelectField('Schedule Type', choices=[
        ('regular', 'Regular Shift'),
        ('overtime', 'Overtime'),
        ('on-call', 'On Call')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(ScheduleForm, self).__init__(*args, **kwargs)
        self.staff_id.choices = [(s.id, f"{s.full_name} ({s.position})") for s in Staff.query.filter_by(is_active=True).all()]
        