from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import (
    login_required,
    fresh_login_required
)
import google.auth.transport.requests
import google.oauth2.id_token
import os, requests, json, time, datetime
from google import pubsub_v1

returns = Blueprint('returns', __name__, template_folder='templates')

def exe_cloud_function(cloud_function, lat, lon):
    
    # needed to be set
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "keys/pccwebclient.json"

    # create credential to get the token for API
    cred = google.oauth2.id_token.fetch_id_token_credentials(cloud_function)
    # get the ID_Token
    cred.refresh(google.auth.transport.requests.Request())

    # set function body
    payload = {
        'lat': str(lat),
        'lon': str(lon)
    }

    # trigger cloud function
    res = requests.post(cloud_function, json=payload, headers={"Authorization": f"Bearer {cred.token}"})

    # if it is all ok, return the veichle
    if(res.status_code) == 200:
        return res.content.decode("UTF-8")
    else: 
        print(res.content)
        return None

def sample_pull(vehicle_num):
    # Create a client
    client = pubsub_v1.SubscriberClient.from_service_account_file("keys/pccwebclient.json")
    
    # Initialize request argument(s)
    request = pubsub_v1.PullRequest(
        subscription="projects/pccreverselogistic/subscriptions/vehicle_realtime_positions",
        max_messages=100
    )

    # Make the request
    response = client.pull(request=request)
    
    
    # get last message
    
    data_to_send = "No Data"
    messageTime = 0
    message_idx = -1
    
    # iterate over the messages
    for idx, m in enumerate(response.received_messages):
        # check for the right vehicle
        if (m.message.attributes["subFolder"] == vehicle_num):
            # get sent data
            message_payload = json.loads(m.message.data.decode("UTF-8"))
            # get timestamp
            message_time = time.mktime(datetime.datetime.strptime(message_payload["timestamp"],"%Y-%m-%d %H:%M:%S").timetuple())
            # check if it is the latest message
            if(messageTime <= message_time):
                messageTime = message_time
                message_idx = idx          
        else:
            pass
    # there are message
    if message_idx > -1:
        data_to_send = json.loads(response.received_messages[message_idx].message.data.decode("UTF-8"))  
    
    return json.dumps(data_to_send)


# get return page to do the return
@returns.route('/')
# protected route
@login_required
def returns_page():
    return render_template("returns.html")


# get vehicle API
@returns.route('/getvehicle')
@login_required
def return_vehicle():
    
    # here we want to get the value of user (i.e. ?user=some-value)
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    # get cloud function path from the enviroment
    if(os.environ.get("CLOUD_FUNCTION") != None):
        cloud_function = os.environ.get("CLOUD_FUNCTION")
    else:
        cloud_function = "https://europe-west1-pccreverselogistic.cloudfunctions.net/get_vehicle"

    # if there aren't the query params respond with bad request
    if (lat != None and lon != None):
        
        # run cloud function and get the vehicle
        vehicle = exe_cloud_function(cloud_function, lat, lon)
        
        # if no response is retrived
        if vehicle == None:
            return "Error in getting the vehicle", 500
        else:
            return vehicle, 200
    else:
        return "Bad Request, insert lat and lon query params", 400


# get vehicle data
@returns.route('/getvehicleposition')
@login_required
def get_vehicle_position():
    data = sample_pull(request.args.get('vehicle'))
    return data, 200