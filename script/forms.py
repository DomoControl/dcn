from wtforms import *
import wtforms
from wtforms.validators import DataRequired
print dir(wtforms)
 
class ContactForm(Form):
    name = StringField('name', validators=[DataRequired()])
