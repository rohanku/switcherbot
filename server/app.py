from decouple import config

from config import Config
from functools import wraps
import json
from os import environ as env
from werkzeug.exceptions import HTTPException

from dotenv import load_dotenv, find_dotenv
from flask import Flask, redirect, render_template, session, url_for, request, flash
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode

from flask_migrate import Migrate
from errors import RegistryExistsException
import db
import iot

app = Flask(__name__)
app.config.from_object(Config)

oauth = OAuth(app)

auth0 = oauth.register(
    'auth0',
    client_id=Config.AUTH0_CLIENT_ID,
    client_secret=Config.AUTH0_CLIENT_SECRET,
    api_base_url='https://dev-jh3udjni.us.auth0.com',
    access_token_url='https://dev-jh3udjni.us.auth0.com/oauth/token',
    authorize_url='https://dev-jh3udjni.us.auth0.com/authorize',
    client_kwargs={
        'scope': 'openid profile email',
    },
)

def requires_auth(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    if 'profile' not in session:
      # Redirect to Login page here
      return redirect(url_for('login'))
    return f(*args, **kwargs)

  return decorated

@app.route('/api/create_registry', methods=['POST'])
def create_registry():
    try:
        registry_id = db.execute(db.create_registry, session['profile']['user_id'], request.form['name'])
        iot.create_registry(f'rg{registry_id}')
    except RegistryExistsException:
        flash("Registry already exists!")
    except:
        flash("An unknown error occured! Please contact a me at rohankumar@berkeley.edu to resolve the issue.")
    finally:
        return redirect(url_for('dashboard'))

@app.route('/api/login')
def callback():
    # Handles response from token endpoint
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    # Store the user information in flask session.
    session['jwt_payload'] = userinfo
    session['profile'] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'picture': userinfo['picture']
    }
    return redirect(url_for('dashboard'))

@app.route('/')
def home():
    if 'profile' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/login')
def login():
    return auth0.authorize_redirect(redirect_uri=url_for('callback', _external=True))

# /server.py

@app.route('/dashboard')
@requires_auth
def dashboard():
    registries = db.execute(db.get_registries, session['profile']['user_id'])
    return render_template('dashboard.html',
                           userinfo=session['profile'],
                           userinfo_pretty=json.dumps(session['jwt_payload'], indent=4),
                           registries=registries)

@app.route('/logout')
def logout():
    # Clear session stored data
    session.clear()
    # Redirect user to logout endpoint
    params = {'returnTo': url_for('home', _external=True), 'client_id': Config.AUTH0_CLIENT_ID}
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))

if __name__ == "__main__":
    app.run()

