from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Uživatelské jméno', validators=[DataRequired()])
    password = PasswordField('Heslo', validators=[DataRequired()])
    remember_me = BooleanField('Zůstat přihlášen')

class RegisterForm(FlaskForm):
    username = StringField('Uživatelské jméno', validators=[
        DataRequired(), 
        Length(min=3, max=20, message='Uživatelské jméno musí mít 3-20 znaků')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Heslo', validators=[
        DataRequired(), 
        Length(min=6, message='Heslo musí mít alespoň 6 znaků')
    ])
    password2 = PasswordField('Potvrdit heslo', validators=[
        DataRequired(), 
        EqualTo('password', message='Hesla se neshodují')
    ])
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Toto uživatelské jméno už je používáno.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Tento email už je registrovaný.')

class NoteForm(FlaskForm):
    title = StringField('Název poznámky', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Obsah poznámky', validators=[DataRequired()])
    subject = SelectField('Předmět', choices=[], coerce=str, validators=[])
    tags = StringField('Tagy (oddělené čárkou)', validators=[Length(max=500)])