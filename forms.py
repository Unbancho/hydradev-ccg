from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, ValidationError
from models import User

#import wtforms_json

#wtforms_json.init()

class AuthenticationForm(FlaskForm):
    username = StringField(validators=[InputRequired()], render_kw={"placeholder": 'Username'})
    password = PasswordField(validators=[InputRequired()], render_kw={"placeholder": 'Password'})



class SignUpForm(AuthenticationForm):
    real_name = StringField(validators=[InputRequired()], render_kw={"placeholder": 'Full name'})
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        query = User.query().filter_by(username=username.data).first()
        if query:
            raise ValidationError("Someone has already registered with that username. Enter a different username.")

class LoginForm(AuthenticationForm):
    submit = SubmitField("Sign In")

#class DeckForm(FlaskForm):
