from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired, Regexp


class RegisterForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Regexp(r'^[A-Za-z0-9_]+$')])
    about = StringField("Briefly about yourself", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    password_again = PasswordField("Repeat the password", validators=[DataRequired()])
    submit = SubmitField("Register")