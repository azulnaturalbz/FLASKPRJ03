from flask_wtf import Form
from wtforms import PasswordField
from wtforms import SubmitField
from wtforms.fields.html5 import EmailField
from wtforms import validators
from wtforms import TextField


class RegistrationForm(Form):
    email = EmailField('email',validators=[validators.DataRequired(),
                                           validators.Email()])
    password = PasswordField('password',validators=[validators.DataRequired(),
                                                    validators.Length(min=8, message="Please choose a password of 8 characters")])
    password2 = PasswordField('password2',validators=[validators.DataRequired(),
                                                      validators.EqualTo('password',message="Passwords must match")])
    submit = SubmitField('submit',[validators.DataRequired()])


class LoginForm(Form):
    loginemail = EmailField('email',validators=[validators.DataRequired(),
                                           validators.Email(message="Please enter an email")])
    loginepassword = PasswordField('password',validators=[validators.DataRequired(message="Password field required")])

    submit = SubmitField('submit',[validators.DataRequired()])

class CreateTableForm(Form):
    table_number = TextField('tablenumber',validators=[validators.DataRequired()])

    submit = SubmitField('createtablesubmit',validators=[validators.DataRequired()])


