from wtforms import (
	Form,
	IntegerField,
	)
from wtforms.validators import (
	DataRequired,
	NumberRange
	)

class GameCreateForm(Form):
    size = IntegerField('Size of matrix', [DataRequired(), 
						NumberRange(min=3, max=10)], default=3)