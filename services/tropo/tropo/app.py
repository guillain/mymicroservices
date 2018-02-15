#! /usr/bin/python
'''
    Tropo WebAPI Endpoint for Simple Superhero Voting Application

    This is a WebAPI Service for Cisco Tropo to respond to Text or Voice based
    interaction withe the MyHero Application.  Users can
    check current standings, list the available options, and place a vote.

    This is the an example Service for a basic microservice demo application.
    The application was designed to provide a simple demo for Cisco Mantl

    There are several pieces of information needed to run this application.  It is
    suggested to set them as OS Environment Variables.  Here is an example on how to
    set them:

    # Address and key for app server
    export myhero_app_server=http://myhero-app.mantl.domain.com
    export myhero_app_key=DemoAppKey
    export myhero_tropo_secret=DevTropo
    export myhero_tropo_user=tropouser
    export myhero_tropo_pass=tropopass
    export myhero_tropo_prefix=1419
    export myhero_tropo_url=http://localhost:5000



'''

__author__ = 'hapresto'

# Todo - Convert back to flask "json.dumps(page.json)"


# from flask import Flask, request, Response
import requests, json, re
from requests.auth import HTTPBasicAuth
from itty import *
from tropo import Tropo, Session

# app = Flask(__name__)

# Tropo API Details
tropo_host = "https://api.tropo.com/v1"
tropo_headers = {}
tropo_headers["Content-type"] = "application/json"

# MyHero APP Details
app_headers = {}
app_headers["Content-type"] = "application/json"


# @app.route('/', methods=["POST"])
@post('/')
def index(request):
    t = Tropo()

    # s = Session(request.get_json(force=True))
    sys.stderr.write(str(request.body) + "\n")

    s = Session(request.body)
    message = s.initialText
    # print("Initial Text: " + initialText)

    # Check if message contains word "results" and if so send results
    if not message:
        # number = s["session"]["parameters"]["numberToDial"]
        number = s.parameters["numberToDial"]
        reply = "Would you like to vote?"
        t.call(to=number, network="SMS")
        # t.say(reply)

    elif message.lower().find("results") > -1:
        results = get_results()
        reply = ["The current standings are"]
        for i, result in enumerate(results):
            if i == 0:
                reply.append("  *** %s is in the lead with %s percent of the votes.\n" % (result[0], str(round(result[2]))))
            elif i <= 3:
                reply.append("  -   %s has %s percent of the votes.\n" % (result[0], str(round(result[2]))))
    # Check if message contains word "options" and if so send options
    elif message.lower().find("options") > -1:
        options = get_options()
        reply = ["The options are..."]
        msg = ""
        for option in options:
            msg += "%s, " % (option)
        msg = msg[:-2] + ""
        reply.append(msg)
    # Check if message contains word "vote" and if so start a voting session
    elif message.lower().find("vote") > -1:
        # reply = "Let's vote!  Look for a new message from me so you can place a secure vote!"
        reply = [process_incoming_message(message)]
    # If nothing matches, send instructions
    else:
        # Reply back to message
        # reply = "Hello, welcome to the MyHero Demo Room.\n" \
        #         "To find out current status of voting, ask 'What are the results?'\n" \
        #         "To find out the possible options, ask 'What are the options?\n" \
        #         '''To place a vote, simply type the name of your favorite Super Hero and the word "vote".'''
        reply = ["Hello, welcome to the MyHero Demo Room." ,
                "To find out current status of voting, ask 'What are the results?'",
                "To find out the possible options, ask 'What are the options?",
                '''To place a vote, simply type the name of your favorite Super Hero and the word "vote".''']

    # t.say(["Really, it's that easy." + message])
    t.say(reply)
    response = t.RenderJson()
    sys.stderr.write(response + "\n")
    return response

@get('/application')
def display_tropo_application(request):
    # Verify that the request is propery authorized
    authz = valid_request_check(request)
    if not authz[0]:
        return authz[1]

    return json.dumps(demoapp)

@get('/application/number')
def display_tropo_application_number(request):
    # Verify that the request is propery authorized
    authz = valid_request_check(request)
    if not authz[0]:
        return authz[1]

    addresses = get_application_addresses(demoapp)
    numbers = []
    for address in addresses:
        if address["type"] == "number":
            numbers.append(address["number"])
    return json.dumps(numbers)
    # return json.dumps(demoappnumber)

@get('/hello/(?P<number>\w+)')
def send_hello(request, number):
    sys.stderr.write("Sending hello to: " + number + "\n")
    message = "Hello, would you like to vote?"

    u = tropo_host + "/sessions?action=create&token=%s&numberToDial=%s&msg=%s" % (demoappmessagetoken, number, message)
    page = requests.get(u, headers=tropo_headers)
    # ToDo - For some reason the returned page isn't decoding properly.  Not needed to work, fix later
    # result= page.json()
    # sys.stderr.write(json.dumps(result) + "\n")

    headers = [
        ('Access-Control-Allow-Origin', '*')
    ]
    response = Response('Message sent to ' + number, headers=headers)
    return response

@get('/health')
def health_check(request):
    headers = [
        ('Access-Control-Allow-Origin', '*')
    ]
    response = Response('Service Up.', headers=headers)
    return response


# Utilities to interact with the MyHero-App Server
def get_results():
    u = app_server + "/v2/results"
    page = requests.get(u, headers = app_headers)
    tally = page.json()
    return tally

def get_options():
    u = app_server + "/options"
    page = requests.get(u, headers=app_headers)
    options = page.json()["options"]
    return options

def place_vote(vote):
    u = app_server + "/vote/" + vote
    page = requests.post(u, headers=app_headers)
    return page.json()

# Figure out who to vote for
def process_incoming_message(message):
    # What to do...
    # 1.  Get Possible Options
    # 2.  See if the message contains one of the options
    # 3.  Cast vote for option
    # 4.  Thank the user for their vote
    # 5.  Delete Webhook

    options = get_options()
    chosen_hero = ""
    for option in options:
        if message.lower().find(option.lower()) > -1:
            pprint("Found a vote for: " + option)
            chosen_hero = option
            break

    # Cast Vote
    if chosen_hero != "":
        vote = place_vote(chosen_hero)
        msg = "Thanks for your vote for %s.  Your vote has been recorded and this ends this voting session." % (chosen_hero)
    else:
        msg = "I didn't understand your vote, please type the name of your chosen hero exactly as listed on the ballot.  "
    return msg

# Tropo Utilities
def get_applications():
    tropo_u = tropo_host + "/applications"
    page = requests.get(tropo_u, headers = tropo_headers, auth=HTTPBasicAuth(tropo_user, tropo_pass))
    applications = page.json()
    return applications

def get_application_addresses(application):
    tropo_u = tropo_host + "/applications/%s/addresses" % (application["id"])
    page = requests.get(tropo_u, headers = tropo_headers, auth=HTTPBasicAuth(tropo_user, tropo_pass))
    addresses = page.json()
    return addresses

def create_application(appname, appurl):
    data = {
    "name":appname,
    "voiceUrl":appurl,
    "messagingUrl":appurl,
    "platform":"webapi",
    "partition":"staging"
    }

    tropo_u = tropo_host + "/applications"
    page = requests.post(tropo_u, headers = tropo_headers, auth=HTTPBasicAuth(tropo_user, tropo_pass), json=data)
    appurl = page.json()["href"]

    page = requests.get(appurl, headers = tropo_headers, auth=HTTPBasicAuth(tropo_user, tropo_pass))
    app = page.json()
    return app

def set_application_url(application, appurl):
    data = {
    "name":application["name"],
    "voiceUrl":appurl,
    "messagingUrl":appurl,
    "platform":"webapi",
    "partition":"staging"
    }

    tropo_u = tropo_host + "/applications/%s" % (application["id"])
    page = requests.put(tropo_u, headers = tropo_headers, auth=HTTPBasicAuth(tropo_user, tropo_pass), json=data)
    appurl = page.json()["href"]

    page = requests.get(appurl, headers = tropo_headers, auth=HTTPBasicAuth(tropo_user, tropo_pass))
    app = page.json()
    return app

def add_number(application, prefix):
    data = {
    "type":"number",
    "prefix":prefix
    }

    tropo_u = tropo_host + "/applications/%s/addresses" % (application["id"])
    page = requests.post(tropo_u, headers = tropo_headers, auth=HTTPBasicAuth(tropo_user, tropo_pass), json=data)
    if page.status_code == 200:
        # Success
        # print page
        addressurl = page.json()["href"]
        page = requests.get(addressurl, headers = tropo_headers, auth=HTTPBasicAuth(tropo_user, tropo_pass))
        address = page.json()
        return address
    else:
        return "Error: Failed to add number to application"

def add_token(application, type="messaging"):
    data = {
    "type":"token",
    "channel": type
    }

    tropo_u = tropo_host + "/applications/%s/addresses" % (application["id"])
    page = requests.post(tropo_u, headers = tropo_headers, auth=HTTPBasicAuth(tropo_user, tropo_pass), json=data)

    # {"href":"https://api.tropo.com/v1/applications/123456/addresses/token/12345679f90bac47a05b178c37d3c68aaf38d5bdbc5aba0c7abb12345d8a9fd13f1234c1234567dbe2c6f63b"}
    if page.status_code == 200:
        # Success
        # print page
        addressurl = page.json()["href"]
        page = requests.get(addressurl, headers = tropo_headers, auth=HTTPBasicAuth(tropo_user, tropo_pass))
        address = page.json()
        return address
    else:
        return "Error: Failed to add number to application"


def get_exchanges():
    # Example Exchange
    # {u'amountNumbersToOrder': 25,
    #  u'areaCode': u'443',
    #  u'city': u'Aberdeen',
    #  u'country': u'United States',
    #  u'countryDialingCode': u'1',
    #  u'description': u'',
    #  u'href': u'https://api.tropo.com/rest/v1/exchanges/2142',
    #  u'id': 2142,
    #  u'minNumbersInExchange': 10,
    #  u'prefix': u'1443',
    #  u'requiresVerification': False,
    #  u'state': u'MD',
    #  u'tollFree': False}
    tropo_u = tropo_host + "/exchanges"
    page = requests.get(tropo_u, headers = tropo_headers, auth=HTTPBasicAuth(tropo_user, tropo_pass))
    exchanges = page.json()
    return exchanges

def get_available_numbers(exchange):
    # Example Exchange
    #  {u'city': u'Aberdeen',
    # u'country': u'United States',
    # u'displayNumber': u'+1 443-863-7082',
    # u'href': u'https://api.tropo.com/rest/v1/addresses/number/+14438637082',
    # u'number': u'+14438637082',
    # u'prefix': u'1443',
    # u'smsEnabled': True,
    # u'state': u'MD',
    # u'subscriber': False,
    # u'type': u'number'}
    tropo_u = tropo_host + "/addresses?available=true&type=NUMBER&prefix=%s" % (exchange)
    page = requests.get(tropo_u, headers = tropo_headers, auth=HTTPBasicAuth(tropo_user, tropo_pass))
    numbers = page.json()
    sms_numbers = []
    for number in numbers:
        if number["smsEnabled"]:
            sms_numbers.append(number)
    return sms_numbers

def test_exchange(exchange):
    exchanges = get_available_numbers(exchange)
    if len(exchanges) > 0:
        return True
    else:
        return False


# Standard Utility
def valid_request_check(request):
    try:
        if request.headers["key"] == secret_key:
            return (True, "")
        else:
            error = {"Error": "Invalid Key Provided."}
            print error
            status = 401
            resp = Response(json.dumps(error), content_type='application/json', status=status)
            return (False, resp)
    except KeyError:
        error = {"Error": "Method requires authorization key."}
        print error
        status = 400
        resp = Response(json.dumps(error), content_type='application/json', status=status)
        return (False, resp)




if __name__ == '__main__':
    from argparse import ArgumentParser
    import os, sys
    from pprint import pprint

    # Setup and parse command line arguments
    parser = ArgumentParser("MyHero Spark Interaction Bot")
    parser.add_argument(
        "-a", "--app", help="Address of app server", required=False
    )
    parser.add_argument(
        "-k", "--appkey", help="App Server Authentication Key Used in API Calls", required=False
    )
    parser.add_argument(
        "-s", "--secret", help="Key Expected in API Calls", required=False
    )
    parser.add_argument(
        "-t", "--tropouser", help="Tropo Username", required=False
    )
    parser.add_argument(
        "-p", "--tropopass", help="Tropo Password", required=False
    )
    parser.add_argument(
        "--tropoprefix", help="Tropo Number Prefix", required=False
    )
    parser.add_argument(
        "--tropourl", help="Local Address for Tropo App URL", required=False
    )

    args = parser.parse_args()

    app_server = args.app
    # print "Arg App: " + str(app_server)
    if (app_server == None):
        app_server = os.getenv("myhero_app_server")
        # print "Env App: " + str(app_server)
        if (app_server == None):
            get_app_server = raw_input("What is the app server address? ")
            # print "Input App: " + str(get_app_server)
            app_server = get_app_server
    # print "App Server: " + app_server
    sys.stderr.write("App Server: " + app_server + "\n")

    app_key = args.appkey
    # print "Arg App Key: " + str(app_key)
    if (app_key == None):
        app_key = os.getenv("myhero_app_key")
        # print "Env App Key: " + str(app_key)
        if (app_key == None):
            get_app_key = raw_input("What is the app server authentication key? ")
            # print "Input App Key: " + str(get_app_key)
            app_key = get_app_key
    # print "App Server Key: " + app_key
    sys.stderr.write("App Server Key: " + app_key + "\n")

    secret_key = args.secret
    if (secret_key == None):
        secret_key = os.getenv("myhero_tropo_secret")
        if (secret_key == None):
            get_secret_key = raw_input("What is the Authorization Key to Require? ")
            secret_key = get_secret_key
    sys.stderr.write("Secret Key: " + secret_key + "\n")

    tropo_user = args.tropouser
    if (tropo_user == None):
        tropo_user = os.getenv("myhero_tropo_user")
        if (tropo_user == None):
            get_tropo_user = raw_input("What is the Tropo Username? ")
            tropo_user = get_tropo_user
    sys.stderr.write("Tropo User: " + tropo_user + "\n")

    tropo_prefix = args.tropoprefix
    if (tropo_prefix == None):
        tropo_prefix = os.getenv("myhero_tropo_prefix")
        if (tropo_prefix == None):
            get_tropo_prefix = raw_input("What is the Tropo Prefix? ")
            tropo_prefix = get_tropo_prefix
    sys.stderr.write("Tropo Prefix: " + tropo_prefix + "\n")

    tropo_pass = args.tropopass
    if (tropo_pass == None):
        tropo_pass = os.getenv("myhero_tropo_pass")
        if (tropo_pass == None):
            get_tropo_pass = raw_input("What is the Tropo Password? ")
            tropo_pass = get_tropo_pass
    # sys.stderr.write("Tropo Pass: " + tropo_pass + "\n")
    sys.stderr.write("Tropo Pass: REDACTED\n")

    tropo_url = args.tropourl
    if (tropo_url == None):
        tropo_url = os.getenv("myhero_tropo_url")
        if (tropo_url == None):
            get_tropo_url = raw_input("What is the Local Tropo App URL? ")
            tropo_url = get_tropo_url
    sys.stderr.write("Tropo URL: " + tropo_url + "\n")


    # Set Authorization Details for external requests
    app_headers["key"] = app_key

    # Find if Tropo Application "myherodemo" already exists
    # If not, create it
    # If exists, verify has correct url and a number in the correct prefix
    tropo_applications = get_applications()

    demoappname = "myherodemo " + tropo_url[len("http://"):tropo_url.find("-tropo")+len("-tropo")]
    demoappid = ""
    demoapp = {}
    demoappnumbers = []
    demoappnumber = ""
    demoappprefix = ""
    demoappmessagetoken = ""

    for app in tropo_applications:
        if app["name"] == demoappname:
            # pprint("Found Demo App")
            demoappid = app["id"]
            demoapp = app
            if demoapp["messagingUrl"] != tropo_url:
                pprint("Updated App URLs")
                demoapp = set_application_url(demoapp, tropo_url)

    if demoappid == "":
        pprint("Creating Tropo App")
        demoapp = create_application(demoappname, tropo_url)
        demoappid = demoapp["id"]
        # pprint(demoapp)

    pprint("Tropo App: %s - %s" % (demoappid, demoapp["name"]))
    # pprint(demoapp)

    addresses = get_application_addresses(demoapp)
    for address in addresses:
        if address["type"] == "number":
            demoappnumbers.append(address["number"])
            if address["prefix"] == tropo_prefix:
                # pprint("Found Address")
                demoappnumber = address["number"]
                demoappprefix = address["prefix"]
        if address["type"] == "token" and address["channel"] == "messaging":
            demoappmessagetoken = address["token"]

    if demoappmessagetoken == "":
        pprint("Creating a Token")
        token = add_token(demoapp)
        demoappmessagetoken = token["token"]
        pprint("Token is: " + demoappmessagetoken)

    if demoappnumber == "":
        if test_exchange(tropo_prefix):
            pprint ("Creating Tropo Number")
            address = add_number(demoapp, tropo_prefix)
            demoappnumber = address["number"]
            demoappprefix = address["prefix"]
            demoappnumbers.append(demoappnumber)
        else:
            sys.stderr.write("Error: No numbers available for prefix %s.\n" % (tropo_prefix))

    sys.stderr.write("Tropo Number: " + ", ".join(demoappnumbers) + "\n")

    # Only run if there is a number available
    if len(demoappnumbers) > 0:
        # app.run(debug=True, host='0.0.0.0', port=int("5000"))
        run_itty(server='wsgiref', host='0.0.0.0', port=5000)
    else:
        sys.stderr.write("Can't start Tropo Service, no numbers deployed to application.\n")
