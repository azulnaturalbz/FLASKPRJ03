from flask import Flask,render_template
from flask_login import LoginManager
from flask_login import login_required

app = Flask(__name__)
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
