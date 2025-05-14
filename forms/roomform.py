from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired, Regexp


class CreateRoomForm(FlaskForm):
    label = StringField("Room label", validators=[DataRequired(), Regexp(r'^[A-Za-z0-9_]+$')])
    about = StringField("Briefly about the room", validators=[DataRequired()])
    submit = SubmitField("Create the room")