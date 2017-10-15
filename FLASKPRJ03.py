from flask import Flask,render_template
from flask import redirect
from flask import url_for
from flask_login import LoginManager
from flask_login import login_required
from USER import User
from MOCKDBHELPER import MockDBHelper as DBHelper


app = Flask(__name__)
app.secret_key = 'tPXJY3X37Qybz4QykV+hOyUxVQeEXf1Ao2C8upz+fGQXKsM'
DB = DBHelper
login_manager = LoginManager(app)

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/account')
@login_required
def account():
    return "You are free"


if __name__ == '__main__':
    app.run()
