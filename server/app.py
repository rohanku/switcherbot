from decouple import config

from config import Config
from functools import wraps
import json
from os import environ as env
from werkzeug.exceptions import HTTPException

from dotenv import load_dotenv, find_dotenv
from flask import Flask, redirect, render_template as flask_render_template, session, url_for, request, flash
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode

from flask_migrate import Migrate
from google.api_core.exceptions import FailedPrecondition
from errors import HandledException, RegistryExistsException
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

def render_template(*args, **kwargs):
    if 'profile' in session:
        registries = db.execute(db.get_registries, session['profile']['user_id'])
        devices = {}
        for registry in registries:
            devices[registry[0]] = db.execute(db.get_devices, registry[0])
        return flask_render_template(*args, **kwargs,
                               userinfo=session['profile'],
                               registries=registries,
                               devices=devices,
                               segment=args[0])
    else:
        return flask_render_template(*args, **kwargs, segment=args[0])

@app.errorhandler(403)
def handle_error(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def handle_error(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def handle_error(e):
    return render_template('errors/500.html'), 500

def requires_auth(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    if 'profile' not in session:
      # Redirect to Login page here
      return redirect(url_for('login'))
    return f(*args, **kwargs)

  return decorated

@app.route('/api/create_registry', methods=['POST'])
@requires_auth
def create_registry():
    try:
        registry_id = db.execute(db.create_registry, session['profile']['user_id'], request.form['name'])
    except RegistryExistsException:
        flash("Registry already exists!")
    except Exception as error:
        flash("An unknown error occured! Please contact me at rohankumar@berkeley.edu to resolve the issue.")
        print(error)
    finally:
        return redirect(url_for('dashboard'))

@app.route('/api/update_registry', methods=['POST'])
@requires_auth
def update_registry():
    try:
        admin = db.execute(db.is_admin, session['profile']['user_id'], request.form['id'])
        if not admin:
            flash("You do not have permissions to add a update that registry!")
            raise HandledException
        db.execute(db.update_registry_info, request.form['id'], request.form['name'])
    except HandledException:
        pass
    except Exception as error:
        flash("An unknown error occured! Please contact me at rohankumar@berkeley.edu to resolve the issue.")
        print(error)
    finally:
        return redirect(url_for('home_detail', registry_id=request.form['id']))

@app.route('/api/add_device', methods=['POST'])
@requires_auth
def add_device():
    try:
        admin = db.execute(db.is_admin, session['profile']['user_id'], request.form['registry_id'])
        if not admin:
            flash("You do not have permissions to add a device to that registry!")
            raise HandledException
        device_info = db.execute(db.get_device_info, request.form['id'])
        if not device_info:
            flash("That device does not exist!")
            raise HandledException
        if device_info[1]:
            flash("That device has already been registered!")
            raise HandledException
        db.execute(db.update_device_info, request.form['id'], request.form['registry_id'])
    except HandledException:
        pass
    except Exception as error:
        flash("An unknown error occured! Please contact me at rohankumar@berkeley.edu to resolve the issue.")
        print(error)
    finally:
        return redirect(url_for('dashboard'))

@app.route('/api/device_command', methods=['POST'])
@requires_auth
def device_command():
    try:
        has_access = db.execute(db.has_access, session['profile']['user_id'], request.form['registry_id'])
        if not has_access:
            flash("You do not have permissions to send commands to that device!")
            raise HandledException
        device_info = db.execute(db.get_device_info, request.form['device_id'])
        if request.form['registry_id'] != str(device_info[1]):
            flash("You do not have permissions to send commands to that device!")
            raise HandledException
        iot.device_command(str(device_info[0]), request.form['command'])
    except HandledException:
        pass
    except FailedPrecondition:
        flash("That device is not connected!")
    except Exception as error:
        flash("An unknown error occured! Please contact me at rohankumar@berkeley.edu to resolve the issue.")
        print(error, type(error).__name__)
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
    return render_template('landing.html')

@app.route('/login')
def login():
    return auth0.authorize_redirect(redirect_uri=url_for('callback', _external=True))

@app.route('/dashboard')
@requires_auth
def dashboard():
    return render_template('dashboard.html')

@app.route('/homes/<registry_id>')
@requires_auth
def home_detail(registry_id):
    registry_info = db.execute(db.get_registry_info, registry_id)
    admin = db.execute(db.is_admin, session['profile']['user_id'], registry_id)
    members = db.execute(db.get_members, registry_id)
    return render_template('home_detail.html', registry_info=registry_info, admin=admin, members=members)

@app.route('/logout')
def logout():
    # Clear session stored data
    session.clear()
    # Redirect user to logout endpoint
    params = {'returnTo': url_for('home', _external=True), 'client_id': Config.AUTH0_CLIENT_ID}
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))

if __name__ == "__main__":
    app.run()

