from flask import Flask,render_template
from flask import redirect
from flask import url_for
from flask import request
from flask_login import LoginManager
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
from flask_login import current_user
from USER import User
from FORMS import RegistrationForm
from FORMS import LoginForm
from FORMS import CreateTableForm
from PASSWORDHELPER import PasswordHelper
from BITlYHELPER import BitlyHelper
import datetime
import CONFIG
if CONFIG.test:
    from MOCKDBHELPER import MockDBHelper as DBHelper
else:
    from DBHELPER import DBHelper


app = Flask(__name__)
app.secret_key = 'tPXJY3X37Qybz4QykV+hOyUxVQeEXf1Ao2C8upz+fGQXKsM'
DB = DBHelper()
PH= PasswordHelper()
BH = BitlyHelper()
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    user_password = DB.get_user(user_id)
    if user_password:
        return User(user_id)

@app.route('/login',methods=['POST'])
def login():
    form = LoginForm(request.form)
    if form.validate():
        stored_user = DB.get_user(form.loginemail.data)
        if stored_user and PH.validate_password(form.loginepassword.data,stored_user['salt'],stored_user['hashed']):
            user = User(form.loginemail.data)
            login_user(user,remember=True)
            return redirect(url_for('account'))
        form.loginemail.errors.append("Email or password invalid")
    return render_template("home.html",loginform = form, registrationform=RegistrationForm())

@app.route('/register', methods=['POST'])
def register():
    form = RegistrationForm(request.form)
    if form.validate():
        if DB.get_user(form.email.data):
            form.email.errors.append("Email already taken please try again")
            return render_template('home.html',registrationform=form,loginform=LoginForm())
        salt = PH.get_salt()
        hashed = PH.get_hash(form.password2.data + salt)
        DB.add_user(form.email.data,salt,hashed)
        return render_template('home.html', registrationform=form,loginform=LoginForm(),
                               onloadmessage="Registation Successful you can now login")
    return render_template('home.html',registrationform=form,loginform=LoginForm())


@app.route('/')
def home():
    registrationform = RegistrationForm()
    return render_template('home.html',registrationform=registrationform,loginform=LoginForm())


@app.route('/account')
@login_required
def account():
    tables = DB.get_tables(current_user.get_id())
    return render_template('accounts.html',tables=tables,createtableform=CreateTableForm())


@app.route('/dashboard')
@login_required
def dashboard():
    now = datetime.datetime.now()
    requests = DB.get_requests(current_user.get_id())
    for  req in requests:
        deltaseconds = (now - req['time']).seconds
        req['wait_minutes'] = "{}.{}".format((deltaseconds/60),str(deltaseconds%60).zfill(2))
    return render_template('dashboard.html',requests=requests)


@app.route("/dashboard/resolve")
@login_required
def dashboard_resolve():
    request_id = request.args.get("request_id")
    DB.delete_request(request_id)
    return redirect(url_for('dashboard'))



@app.route("/account/createtable", methods=["POST"])
@login_required
def account_createtable():
    form = CreateTableForm(request.form)
    if form.validate():
        tableid = DB.add_table(form.table_number.data,current_user.get_id())
        new_url = BH.shorten_url(CONFIG.base_url + "newrequest/" + str(tableid))
        DB.update_table(tableid, new_url)
        return redirect(url_for('account'))
    return render_template("accounts.html",createtableform=form,tables=DB.get_table(current_user.get_id()))


@app.route("/account/deletetable")
@login_required
def account_deletetable():
    tableid = request.args.get("tableid")
    DB.delete_table(tableid)
    return redirect(url_for('account'))

@app.route("/newrequest/<tid>")
def new_request(tid):
    if DB.add_request(tid, datetime.datetime.now()):
        return "Your request has been logged and a waiter will be with you shortly"
    return "There is already a request pending for this table. Please be patient, a waiter will be there ASAP"


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run()
