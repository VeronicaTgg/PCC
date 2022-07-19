import requests
import json
import os
from flask import ( 
    Flask, 
    render_template,
    request,
    redirect,
    url_for,
) 
from oauthlib.oauth2 import WebApplicationClient
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from classes.db import get_db
from classes import db
from classes.user import User
import copy

# import blueprints
from blueprints.returns import returns

 # create new app
app = Flask(__name__)


# if production set env variables from os.environ
if app.config["ENV"] == 'production':
    # Google OAuth configs
    GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
    GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
    GOOGLE_DISCOVERY_URL = os.environ["GOOGLE_DISCOVERY_URL"]
    # set cookies duration
    app.config['REMEMBER_COOKIE_DURATION'] = int(os.environ["REMEMBER_COOKIE_DURATION"])
    # set secret key to sign cookies for session handling
    app.secret_key = os.environ["SECRET_KEY"]
else:
    # testing purposes
    GOOGLE_CLIENT_ID="759371413830-mm96r476fnauvtnsrsiejjvamlf94b5c.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET="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"
    GOOGLE_DISCOVERY_URL="https://accounts.google.com/.well-known/openid-configuration"
    # to reload html templates
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    # the session token last for 1h
    app.config['REMEMBER_COOKIE_DURATION'] = 3600
    # set secret key to sign cookies for session handling
    app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
    

# BLUEPRINTS
app.register_blueprint(returns, url_prefix='/returns')

# User session management setup
login_manager = LoginManager()
login_manager.init_app(app)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# get json of google important urls 
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@app.route("/login")
def login():
    # get urls from google
    google_provider_cfg = get_google_provider_cfg()
    # get authorization endpoint url
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # use OAuth client library to construct the request to google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        # after google authenticate user, go back to this url of the app
        redirect_uri=request.base_url + "/callback",
        # set what kind of information google has to retreive
        scope=["openid", "email", "profile"],
    )
    # send the client to google auth site
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    # get the google authorizzation code (the user accepted to pass the information to the app)
    code = request.args.get("code")
    # get the url to get the token for future api request
    google_provider_cfg = get_google_provider_cfg()
    # get the path to get the token
    token_endpoint = google_provider_cfg["token_endpoint"]
    # Prepare and send a request to get tokens
    token_url, headers, body = client.prepare_token_request(
        # request endpoint
        token_endpoint,
        # the google url where the user agreed 
        authorization_response=request.url,
        # required by docs
        redirect_url=request.base_url,
        # the code retrieved by google after the consens
        code=code
    )
    # do the request for the token
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # get the token from the response body
    client.parse_request_body_response(json.dumps(token_response.json()))

    # get the userinfo endpoint
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    # use OAuth Client to prepare the api requet to google api
    uri, headers, body = client.add_token(userinfo_endpoint)
    # request the information to google api
    userinfo_response = requests.get(uri, headers=headers, data=body)
    # get the info
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
        users_locale = userinfo_response.json()["locale"]
    else:
        return "User email not available or not verified by Google.", 400

    # only UNIMORE student can access
    if users_email.split("@")[1] not in ["studenti.unimore.it", "unimore.it"]:
        return redirect(url_for("only_unimore"))
    
    # create a new user istance
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture, locale=users_locale
    )

    # if the user not exists create it on the db
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture, users_locale )

    # pass the new user to flasklogin, and remember the user with a cookie
    login_user(user, remember=True)

    return redirect(url_for("index"))

# when a user is unauthorized
@login_manager.unauthorized_handler
def unauthorized():
    return render_template("login.html")

# logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

# home
@app.route("/")
def index():        
    return render_template("home.html")

# only unimore page
@app.route("/onlyunimore")
def only_unimore():        
    return render_template("only_unimore.html")

# handler function for 404 routes
def handle_not_found_requests(e):
    return render_template("not_found_404.html")

# register handler
app.register_error_handler(404, handle_not_found_requests)

# if file is runned from cmd and not from flask command
if __name__ == "__main__":
    app.run()
    # app.run(ssl_context='adhoc')