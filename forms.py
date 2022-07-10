from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired


class AuthenticationForm(FlaskForm):
    username = StringField(validators=[InputRequired()], render_kw={"placeholder": 'Username'})
    password = PasswordField(validators=[InputRequired()], render_kw={"placeholder": 'Password'})


class RegisterForm(AuthenticationForm):
    real_name = StringField(validators=[InputRequired()], render_kw={"placeholder": 'Full name'})
    submit = SubmitField("Sign Up")


class LoginForm(AuthenticationForm):
    submit = SubmitField("Sign In")
