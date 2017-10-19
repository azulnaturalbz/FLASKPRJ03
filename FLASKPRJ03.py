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
from MOCKDBHELPER import MockDBHelper as DBHelper
from PASSWORDHELPER import PasswordHelper
from BITlYHELPER import BitlyHelper
import CONFIG

import json
import urllib2
import urllib
import feedparser
import datetime
from flask import make_response

app = Flask(__name__)
app.secret_key = 'tPXJY3X37Qybz4QykV+hOyUxVQeEXf1Ao2C8upz+fGQXKsM'
DB = DBHelper()
PH= PasswordHelper()
BH = BitlyHelper()
login_manager = LoginManager(app)

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/account')
@login_required
def account():
    tables = DB.get_tables(current_user.get_id())
    return render_template('accounts.html',tables=tables)


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')



@app.route('/login',methods=['POST'])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    stored_user = DB.get_user(email)
    if stored_user and PH.validate_password(password, stored_user['salt'], stored_user['hashed']):
        user = User(email)
        login_user(user, remember=True)
        return redirect(url_for('account'))
    return home

@login_manager.user_loader
def load_user(user_id):
    user_password = DB.get_user(user_id)
    if user_password:
        return User(user_id)

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get("email")
    pw1 = request.form.get("password")
    pw2 = request.form.get("password2")
    if not pw1 == pw2:
        return redirect(url_for('home'))
    if DB.get_user(email):
        return redirect(url_for('home'))
    salt = PH.get_salt()
    hashed = PH.get_hash(pw1+salt)
    DB.add_user(email, salt, hashed)
    return redirect(url_for('home'))


@app.route("/account/createtable", methods=["POST"])
@login_required
def account_createtable():
    tablename = request.form.get("tablenumber")
    tableid = DB.add_table(tablename, current_user.get_id())
    new_url = BH.shorten_url(CONFIG.base_url + "newrequest/" + tableid)
    DB.update_table(tableid, new_url)
    return redirect(url_for('account'))


@app.route("/account/deletetable")
@login_required
def account_deletetable():
    tableid = request.args.get("tableid")
    DB.delete_table(tableid)
    return redirect(url_for('account'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))
#
RSS_FEEDS = {'bbn': 'https://www.breakingbelizenews.com/feed/',
             'lov': 'http://lovefm.com/feed/',
             'amd': 'http://amandala.com.bz/news/feed/',
             'sps': 'https://www.sanpedrosun.com/feed/',
             'rpt': 'http://www.reporter.bz/feed/',
             'mybz':'http://www.mybelize.net/feed/'}

DEFAULTS = {'publication': 'bbn',
            'city': 'Belize,bz',
            'currency_from': 'BZD',
            'currency_to': 'USD'}

WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather?q={}&units=metric&APPID=f47aeab3995ca500141e77a82f634ba6"
CURRENCY_URL = "https://openexchangerates.org//api/latest.json?app_id=3939e9bcc6ab47719d6da46537c431e6"


def get_value_with_fallback(key):
    if request.args.get(key):
        return request.args.get(key)
    if request.cookies.get(key):
        return request.cookies.get(key)
    return DEFAULTS[key]


@app.route("/news")
@login_required
def news():
# get cust headlines , based on user input or default
    publication = get_value_with_fallback("publication")
    articles=get_news(publication)
#    publication = request.args.get("publication")
#    if not publication:
#        publication = request.cookies.get("publication")
#        if not publication:
#            publication = DEFAULTS['publication']
#    articles = get_news(publication)
# get cust weather based on user input or default
    city = get_value_with_fallback("city")
    weather = get_weather(city)
#    city = request.args.get('city')
#    if not city:
#        city = DEFAULTS['city']
#    weather = get_weather(city)
# get customized currency from user input or default
    currency_from = get_value_with_fallback("currency_from")
    currency_to = get_value_with_fallback("currency_to")
    rate, currencies = get_rate(currency_from, currency_to)
#    currency_from = request.args.get("currency_from")
#   if not currency_from:
#       currency_from = DEFAULTS['currency_from']
#   currency_to = request.args.get("currency_to")
#    if not currency_to:
#        currency_to = DEFAULTS['currency_to']
#    rate, currencies = get_rate(currency_from, currency_to)

    #return render_template("home.html", articles=articles, weather=weather, currency_from=currency_from,currency_to=currency_to, rate=rate, currencies=sorted(currencies))
    response = make_response(render_template("news.html", articles=articles, weather=weather, currency_from=currency_from,currency_to=currency_to, rate=rate, currencies=sorted(currencies)))
    expires = datetime.datetime.now() + datetime.timedelta(days=365)
    response.set_cookie("publication",publication,expires=expires)
    response.set_cookie("city",city,expires=expires)
    response.set_cookie("currency_from",currency_from,expires=expires)
    response.set_cookie("currency_to",currency_to,expires=expires)
    return response

def get_news(query):
    if not query or query.lower() not in RSS_FEEDS:
        publication = DEFAULTS["publication"]
    else:
        publication = query.lower()
    feed = feedparser.parse(RSS_FEEDS[publication])
    return feed['entries']


def get_weather(query):
    api_url = "http://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid=f47aeab3995ca500141e77a82f634ba6"
    query = urllib.quote(query)
    url = api_url.format(query)
    data = urllib2.urlopen(url).read()
    parsed = json.loads(data)
    weather = None
    if parsed.get("weather"):
        weather = {"description": parsed["weather"][0]["description"],
                   "temperature": parsed["main"]["temp"],
                   "city": parsed["name"],
                   "country": parsed['sys']['country']}
    return weather


def get_rate(frm, to):
    all_currency = urllib2.urlopen(CURRENCY_URL).read()
    parsed = json.loads(all_currency).get('rates')
    frm_rate = parsed.get(frm.upper())
    to_rate = parsed.get(to.upper())
    return to_rate / frm_rate, parsed.keys()

if __name__ == '__main__':
    app.run()
