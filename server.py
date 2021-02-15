#!/usr/bin/env python

import json, os, uuid, requests, msal, app_config, atexit
import blinkt
from datetime import datetime, timedelta
from flask import Flask, jsonify, make_response, Response, request, redirect, session, url_for, send_from_directory, render_template
from flask_session import Session
from flask_apscheduler import APScheduler
from pyngrok import ngrok


#############
# App Setup #
#############

app = Flask(__name__)
app.config.from_object(app_config)
Session(app)

from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

scheduler = APScheduler()
scheduler.api_enabled = True#False
scheduler.init_app(app)
scheduler.start()


###############
# Ngrok Setup #
###############

ngrok.set_auth_token("1lkRMJVY5ULy72xJIQ2pVgbCvY5_6CNYvbLDmsk4bbKkNx1WY")
http_tunnel = ngrok.connect('https://localhost:5000/', bind_tls=True)


#####################
# Blinkt! Hat Setup #
#####################

blinkt.set_clear_on_exit(True)
blinkt.set_brightness(0.2)
blinkt.show()


####################
# Hardware Control #
####################

def switchOff() :
    blinkt.clear()
    blinkt.show()

def setColor(r, g, b) :
    blinkt.set_all(r, g, b)
    blinkt.show()

def getColor() :
    status = blinkt.get_pixel(0)
    return status


###############
# MSAL ROUTES #
###############

@app.route("/")
def index():
    if not session.get("user"):
        return redirect(url_for("login"))
    token = _get_token_from_cache(app_config.SCOPE)
    if not token:
        return redirect(url_for("login"))
    global token_save
    token_save = token['access_token']
    return render_template('index.html', user=session["user"])

@app.route("/login")
def login():
    session["state"] = str(uuid.uuid4())
    auth_url = _build_auth_url(scopes=app_config.SCOPE, state=session["state"])
    return render_template("login.html", auth_url=auth_url, version=msal.__version__)

@app.route(app_config.REDIRECT_PATH)  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized():
    if request.args.get('state') != session.get("state"):
        return redirect(url_for("index"))  # No-OP. Goes back to Index page
    if "error" in request.args:  # Authentication/Authorization failure
        return render_template("auth_error.html", result=request.args)
    if request.args.get('code'):
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_authorization_code(
            request.args['code'],
            scopes=app_config.SCOPE,  # Misspelled scope would cause an HTTP 400 error here
            redirect_uri=url_for("authorized", _external=True))
        if "error" in result:
            return render_template("auth_error.html", result=result)
        session["user"] = result.get("id_token_claims")
        _save_cache(cache)
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()  # Wipe out user and its token cache from session
    return redirect(  # Also logout from your tenant's web session
        app_config.AUTHORITY + "/oauth2/v2.0/logout" +
        "?post_logout_redirect_uri=" + url_for("index", _external=True))

def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        app_config.CLIENT_ID, authority=authority or app_config.AUTHORITY,
        client_credential=app_config.CLIENT_SECRET, token_cache=cache)

def _build_auth_url(authority=None, scopes=None, state=None):
    return _build_msal_app(authority=authority).get_authorization_request_url(
        scopes or [],
        state=state or str(uuid.uuid4()),
        redirect_uri=url_for("authorized", _external=True))

def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        _save_cache(cache)
        return result


#########################
# MSGraph Subscriptions #
#########################

@app.route("/subscriptions")
def get_subscriptions():
    token = _get_token_from_cache(app_config.SCOPE)
    if not token:
        return redirect(url_for("login"))
    global token_save
    token_save = token['access_token']
    graph_data = requests.get(
        app_config.SUBSCRIPTIONS_ENDPOINT,
        headers={'Authorization': 'Bearer ' + token['access_token']}
        ).json()
    if not graph_data.get('value'):
        print("")
        print("> > >")
        print("No Active Subscription")
    else:
        print("")
        print("> > >")
        print("Expires: " + graph_data['value'][0]['expirationDateTime'])
    return make_response(jsonify(graph_data), 202)

@app.route("/create")
def create_subscription():
    token = _get_token_from_cache(app_config.SCOPE)
    if not token:
        return redirect(url_for("login"))
    global token_save
    token_save = token['access_token']
    expireTime = (datetime.utcnow() + timedelta(hours=2)).isoformat() + "Z"
    payload = {
        "changeType": "updated",
        "notificationUrl": http_tunnel.public_url + '/notify',
        # "lifecycleNotificationUrl": http_tunnel.public_url + '/notify',
        "resource": "communications/presences/87cafac4-dd3e-48db-b1f0-63f0788f2ffa",
        "expirationDateTime": expireTime
        }
    graph_data = requests.post(
        app_config.SUBSCRIPTIONS_ENDPOINT,
        headers={
            'Authorization': 'Bearer ' + token['access_token'],
            'Content-Type': 'application/json'},
        json=payload,
        ).json()
    if not graph_data.get('error'):
        print("")
        print("> > >")
        print("Subscription Successful | Expires: " + graph_data.get('expirationDateTime'))
        scheduler.add_job('update_job', update_notification, trigger='interval', minutes=15, misfire_grace_time=30, coalesce=True)
    else:
        print("")
        print("> > >")
        print("Subscription ERROR")
        print(graph_data.get('error'))
    return make_response(jsonify(graph_data), 202)

@app.route("/remove")
def remove_subscription():
    graph_data = requests.get(
        app_config.SUBSCRIPTIONS_ENDPOINT,
        headers={'Authorization': 'Bearer ' + token_save}
        ).json()
    if not graph_data.get('value'):
        print("")
        print("> > >")
        print("No Subscriptions to Remove")
    else:
        removeID = app_config.SUBSCRIPTIONS_ENDPOINT + graph_data['value'][0]['id']
        remove_request = requests.delete(
            removeID,
            headers={'Authorization': 'Bearer ' + token_save}
            )
        print(remove_request)
        print("")
        print("> > >")
        print("Subscription Removed")
    return Response(status=202)

@app.route("/notify", methods=['POST'])
def notification_received():
    valtoken = request.args.get('validationToken')
    graph_data = request.json
    if valtoken != None:
        print("")
        print("> > >")
        print("- - - - - - - - - - - - - - - - - -")
        print("Validation Successful | Valtoken: " + valtoken)
        print("- - - - - - - - - - - - - - - - - -")
        return Response(valtoken, status=200, content_type="text/plain")
    else:
        updatedStatus = graph_data['value'][0]['resourceData']['availability']
        subscriptionID = graph_data['value'][0]['subscriptionId']
        subscriptionExp = graph_data['value'][0]['subscriptionExpirationDateTime']
        if updatedStatus in ["Available", "AvailableIdle"]:
            Available()
        elif updatedStatus in ["Busy", "BusyIdle", "DoNotDisturb"]:
            Busy()
        elif updatedStatus in ["Away", "BeRightBack"]:
            Away()
        elif updatedStatus in ["Offline", "PresenceUnknown"]:
            switchOff()
        else:
            pass
        print("")
        print("> > >")
        print("- - - - - - - - - - - - - - - - - -")
        timeLeftSubscription = (datetime.fromisoformat(subscriptionExp[0:26]) - datetime.now()) - timedelta(hours=2)
        print("Expires in: " + str(timeLeftSubscription))
        print("> > " + updatedStatus.upper() + " < <")
        print("- - - - - - - - - - - - - - - - - -")
        return Response(status=202, mimetype=None)

@app.route("/update", methods=['POST', 'GET'])
def update_notification():
    graph_data = requests.get(
        app_config.SUBSCRIPTIONS_ENDPOINT,
        headers={'Authorization': 'Bearer ' + token_save}
        ).json()
    newExpireTime = (datetime.utcnow() + timedelta(hours=2)).isoformat() + "Z"
    payload = {
        "expirationDateTime": newExpireTime
        }
    sub_ID_ENDPOINT = app_config.SUBSCRIPTIONS_ENDPOINT + graph_data['value'][0]['id']
    update_request = requests.patch(
        sub_ID_ENDPOINT,
        headers={
            'Authorization': 'Bearer ' + token_save,
            'Content-Type': 'application/json'},
        json=payload,
        ).json()
    print("")
    print("> > >")
    print("Subscription Updated")
    return Response(status=202)


####################################
# Original Hardware Control Routes #
####################################


def Busy():
    blinkt.set_all(255, 0, 0)
    blinkt.show()

def Available():
    blinkt.set_all(0, 255, 0)
    blinkt.show()

def Away():
    blinkt.set_all(0, 0, 255)
    blinkt.show()

@app.route('/off')
def apiOff() :
    switchOff()
    scheduler.shutdown(wait=False)
    remove_subscription()
    return Response(status=202)

@app.route('/busy')
def apiBusy() :
    Busy()
    return render_template("index.html", user=session["user"])

@app.route('/available')
def apiAvailable() :
    Available()
    return render_template("index.html", user=session["user"])

@app.route('/away')
def apiAway() :
    Away()
    return render_template("index.html", user=session["user"])

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

atexit.register(lambda: scheduler.shutdown(wait=False))

if __name__ == '__main__':
    app.run(host='0.0.0.0', ssl_context='adhoc')