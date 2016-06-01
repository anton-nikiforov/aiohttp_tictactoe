from wtforms import (
	Form,
	PasswordField,
	StringField,
	)
from wtforms.validators import (
	DataRequired,
	Email,
	EqualTo,
	Length,
	)

class SignInForm(Form):
    login = StringField('Login', [DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', [DataRequired(), Email(), Length(min=6, max=35)])
    password = PasswordField('Password', [
        DataRequired(),
        EqualTo('repassword', message='Passwords must match')
    ])
    repassword = PasswordField('Repeat Password')

class LoginForm(Form):
	email = StringField('Email', [DataRequired(), Email(), Length(min=6, max=35)])
	password = PasswordField('Password', [DataRequired()])