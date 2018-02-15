#! /usr/bin/python
'''
    App Service for Simple Superhero Voting Application

    This is the App Service for a basic microservice demo application.
    The application was designed to provide a simple demo for Cisco Mantl
'''


__author__ = 'hapresto'

from flask import Flask, make_response, request, jsonify, Response
import datetime
import urllib
import json, random
import os, sys, socket, dns.resolver
import requests
import paho.mqtt.publish as publish

# options_cache = ({'options':[]},datetime.datetime.now())
options_cache = False
results_cache = False

app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization,Key')
    # response.headers.add("Access-Control-Expose-Headers", "Total Votes")
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,DELETE,OPTIONS')
    return response


mqtt_host = ""
mqtt_port = 0
mode = "direct"

# Setup MQTT Topic Info
lhost = socket.gethostname()

data_server = None
data_srv = None
mqtt_server = None
mqtt_host = None
mqtt_port = None

@app.route("/health", methods=["GET"])
def health_check():
    return "Service up."

# TODO - Decide if this will be maintaned going forward
@app.route("/hero_list")
def hero_list():
    u = urllib.urlopen(data_server + "/hero_list")
    #sys.stderr.write({}.format(u))
    page = u.read()
    hero_list = json.loads(page)["heros"]

    resp = make_response(jsonify(heros=hero_list))
    return resp

@app.route("/vote/<hero>", methods=["POST"])
def vote(hero):
    if request.method == "POST":
        # Verify that the request is propery authorized
        authz = valid_request_check(request)
        if not authz[0]:
            return authz[1]

        # Depending on mode, either send direct to data server or publish
        if mode == "direct":
            # print("Vote direct")
            u = data_server + "/vote/" + hero
            data_requests_headers = {"key": data_key}

            try:
                page = requests.post(u, headers = data_requests_headers)
            except:
                set_data_server(data_srv)
                u = data_server + "/vote/" + hero
                page = requests.get(u, headers=data_requests_headers)

            result = page.json()["result"]
        elif mode == "queue":
            # print("Vote Q")
            # Publish Message
            publish_vote(hero)
            result = "1"
        if (result == "1"):
            msg = {"result":"vote submitted"}
        else:
            msg = {"result":"vote submission failed"}
        status = 200
        resp = Response(
            json.dumps(msg, sort_keys=True, indent=4, separators=(',', ': ')),
            content_type='application/json',
            status=status)
        return resp

# TODO - Retire this API call
# @app.route("/results")
def results():
    global results_cache

    # Check Cache
    if results_cache and (datetime.datetime.now() - results_cache[1]).seconds < 0:
        #sys.stderr.write("*** Returning Cached Results ***\n")
        tally = results_cache[0]
    else:
        # Get latest data and refresh cache
        try:
            u = urllib.urlopen(data_server + "/results")
            page = u.read()
        except:
            set_data_server(data_srv)
            u = urllib.urlopen(data_server + "/results")
            page = u.read()

        tally = json.loads(page)
        results_cache = (tally, datetime.datetime.now())

    resp = make_response(jsonify(tally))
    resp = Response(
        json.dumps(tally, sort_keys=True, indent = 4, separators = (',', ': ')),
        content_type='application/json', headers={"data_timestamp":str(results_cache[1])},
        status=200)
    return resp

@app.route("/v2/results")
def results_v2():
    # Verify that the request is propery authorized
    authz = valid_request_check(request)
    if not authz[0]:
        return authz[1]

    # ToDo: build cache for v2 results
    # global results_cache
    #
    # # Check Cache
    # if results_cache and (datetime.datetime.now() - results_cache[1]).seconds < 0:
    #     sys.stderr.write("*** Returning Cached Results ***\n")
    #     tally = results_cache[0]
    # else:
    #     # Get latest data and refresh cache
    #     u = urllib.urlopen(data_server + "/results")
    #     page = u.read()
    #     tally = json.loads(page)
    #     results_cache = (tally, datetime.datetime.now())

    # Get latest data and refresh cache
    u = data_server + "/v2/results"
    data_requests_headers = {"key": data_key}

    try:
        page = requests.get(u, headers=data_requests_headers)
    except:
        set_data_server(data_srv)
        u = data_server + "/v2/results"
        page = requests.get(u, headers=data_requests_headers)

    tally = page.json()
    # total_votes = page.headers["Total Votes"]

    resp = Response(
        json.dumps(tally, sort_keys=True, indent=4, separators=(',', ': ')),
        content_type='application/json', headers={"data_timestamp": str(datetime.datetime.now())},
        status=200)
    return resp


@app.route("/options", methods=["GET", "PUT", "POST"])
def options_route():
    '''
    Methods used to view options, add new option, and replace options.
    '''
    # Verify that the request is propery authorized
    authz = valid_request_check(request)
    if not authz[0]:
        return authz[1]

    global options_cache

    u = data_server + "/options"
    if request.method == "GET":
        # Check Cache
        if options_cache and (datetime.datetime.now() - options_cache[1]).seconds < 300:
            sys.stderr.write("*** Returning Cached Options ***\n")
            options = options_cache[0]
            pass
        else:
            # Cache unvailable or expired
            data_requests_headers = {"key": data_key}
            try:
                page = requests.get(u, headers=data_requests_headers)
            except:
                set_data_server(data_srv)
                u = data_server + "/options"
                page = requests.get(u, headers=data_requests_headers)

            options = page.json()
            options_cache = (options, datetime.datetime.now())
        status = 200
    if request.method == "PUT":
        try:
            data = request.get_json(force=True)
            # Verify data is of good format
            # { "option" : "Deadpool" }
            data_requests_headers = {"key": data_key}
            sys.stderr.write("New Option: " + data["option"] + "\n")
            try:
                page = requests.put(u,json = data, headers= data_requests_headers)
            except:
                set_data_server(data_srv)
                u = data_server + "/options"
                page = requests.put(u, json=data, headers=data_requests_headers)

            options = page.json()
            options_cache = (options, datetime.datetime.now())
            status = 201
        except KeyError:
            error = {"Error":"API expects dictionary object with single element and key of 'option'"}
            status = 400
            resp = Response(json.dumps(error), content_type='application/json', status = status)
            return resp
    if request.method == "POST":
        try:
            data = request.get_json(force=True)
            # Verify that data is of good format
            # {
            # "options": [
            #     "Spider-Man",
            #     "Captain America",
            #     "Batman",
            #     "Robin",
            #     "Superman",
            #     "Hulk",
            #     "Thor",
            #     "Green Lantern",
            #     "Star Lord",
            #     "Ironman"
            # ]
            # }
            data_requests_headers = {"key": data_key}
            try:
                page = requests.post(u, json = data, headers = data_requests_headers)
            except:
                set_data_server(data_srv)
                u = data_server + "/options"
                page = requests.post(u, json = data, headers = data_requests_headers)

            options = page.json()
            sys.stderr.write("New Options:" + str(data["options"]) + "\n")
            options_cache = (options, datetime.datetime.now())
            status = 201
        except KeyError:
            error = {"Error": "API expects dictionary object with single element with key 'option' and value a list of options"}
            status = 400
            resp = Response(json.dumps(error), content_type='application/json', status=status)
            return resp

    resp = Response(
        json.dumps(options, sort_keys=True, indent = 4, separators = (',', ': ')),
        content_type='application/json', headers={"data_timestamp":str(options_cache[1])},
        status=status)
    return resp

@app.route("/options/<option>", methods=["DELETE"])
def option_delete_route(option):
    '''
    Delete an option from the the option_list.
    '''
    # Verify that the request is propery authorized
    authz = valid_request_check(request)
    if not authz[0]:
        return authz[1]

    u = data_server + "/options/" + option
    if request.method == "DELETE":
        sys.stderr.write("Delete Option:" + option + "\n")
        data_requests_headers = {"key": data_key}

        try:
            page = requests.delete(u, headers = data_requests_headers)
        except:
            set_data_server(data_srv)
            u = data_server + "/options/" + option
            page = requests.delete(u, headers=data_requests_headers)

        options = page.json()
        status = 202
        resp = Response(
            json.dumps(options, sort_keys=True, indent=4, separators=(',', ': ')),
            content_type='application/json',
            status=status)
        return resp
    else:
        error = {"Error": "Route only acceptes a DELETE method"}
        status = 400
        resp = Response(json.dumps(error), content_type='application/json', status=status)
        return resp

def valid_request_check(request):
    try:
        if request.headers["key"] == app_key:
            return (True, "")
        else:
            error = {"Error": "Invalid Key Provided."}
            sys.stderr.write(str(error) + "\n")
            status = 401
            resp = Response(json.dumps(error), content_type='application/json', status=status)
            return (False, resp)
    except KeyError:
        error = {"Error": "Method requires authorization key."}
        sys.stderr.write(str(error) + "\n")
        status = 400
        resp = Response(json.dumps(error), content_type='application/json', status=status)
        return (False, resp)

def publish_vote(vote):
    # Basic Publish to a MQTT Queue
    # print("Publishing vote.")
    t = lhost + "-" + str(random.randint(0,9))
    try:
        publish.single("MyHero-Votes/" + t, payload=vote, hostname=mqtt_host, port=mqtt_port, retain=True)
    except:
        set_mqtt_server(mqtt_server)
        publish.single("MyHero-Votes/" + t, payload=vote, hostname=mqtt_host, port=mqtt_port, retain=True)

    return ""

# Get SRV Lookup Details for Queueing Server
# The MQTT Server details are expected to be found by processing an SRV Lookup
# The target will be consul for deploments utilizing Mantl.io
# The underlying host running the service must have DNS servers configured to
# Resolve the lookup
def srv_lookup(name):
    resolver = dns.resolver.Resolver()
    results = []
    try:
        for rdata in resolver.query(name, 'SRV'):
            results.append((str(rdata.target), rdata.port))
        # print ("Resolved Service Location as {}".format(results))
    except:
        raise ValueError("Can't find SRV Record")
    return results

# Get IP for Host
def ip_lookup(name):
    resolver = dns.resolver.Resolver()
    results = ""
    try:
        for rdata in resolver.query(name, 'A'):
            results = str(rdata)
        # print ("Resolved Service Location as {}".format(results))
    except:
        raise ValueError("Can't find A Record")
    return results

def set_data_server(data_srv):
    sys.stderr.write("Looking up Data Service Address: %s.\n" % (data_srv))

    global data_server
    # Lookup and resolve the IP and Port for the Data Server by SRV Record
    try:
        records = srv_lookup(data_srv)
        # To find the HOST IP address need to take the returned hostname from the
        # SRV check and do an IP lookup on it
        data_srv_host = str(ip_lookup(records[0][0]))
        data_srv_port = records[0][1]
    except ValueError:
        raise ValueError("Data SRV Record Not Found")
        sys.exit(1)
    # Create data_server format
    data_server = "http://%s:%s" % (data_srv_host, data_srv_port)
    sys.stderr.write("Data Server: " + data_server + "\n")

def set_mqtt_server(mqtt_server):
    sys.stderr.write("Looking up MQTT Service Address: %s.\n" % (mqtt_server))

    global mqtt_host
    global mqtt_port
    # Lookup and resolve the IP and Port for the MQTT Server
    try:
        records = srv_lookup(mqtt_server)
        if len(records) != 1: raise Exception("More than 1 SRV Record Returned")
        # To find the HOST IP address need to take the returned hostname from the
        # SRV check and do an IP lookup on it
        mqtt_host = str(ip_lookup(records[0][0]))
        mqtt_port = records[0][1]
    except ValueError:
        raise ValueError("Message Queue Not Found")
        sys.exit(1)
    sys.stderr.write("MQTT Host: %s \nMQTT Port: %s\n" % (mqtt_host, mqtt_port))

if __name__=='__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser("MyHero Application Service")
    parser.add_argument(
        "-d", "--dataserver", help="Address of data server", required=False
    )
    parser.add_argument(
        "--datasrv", help="Address of data server SRV record", required=False
    )
    parser.add_argument(
        "-k", "--datakey", help="Data Server Authentication Key Used in API Calls", required=False
    )
    parser.add_argument(
        "-s", "--appsecret", help="App Server Key Expected in API Calls", required=False
    )
    parser.add_argument(
        "-q", "--mqttserver", help="MQTT Server FQDN for SRV Lookup", required=False
    )
    parser.add_argument(
        "-i", "--mqtthost", help="MQTT Server Host IP Address", required=False
    )
    parser.add_argument(
        "-p", "--mqttport", help="MQTT Server Port", required=False
    )
    parser.add_argument(
        "--mode", help="Voting Processing Mode - direct or queue", required=False
    )

    parser.add_argument(
        "--port", help="Port to listen on", required=False, default=5000
    )

    args = parser.parse_args()

    # Determine port number
    listen = int(args.port)
    print("Listen: " + str(listen))

    # Priority for Data Server
    # 1. Explicit Data Server Address
    #    1. Arguments
    data_server = args.dataserver
    data_srv = args.datasrv
    # print "Arg Data: " + str(data_server)
    #    2. Env Vars
    if (data_server == None):
        data_server = os.getenv("myhero_data_server")
        # print "Env Data: " + str(data_server)
    # 2. SRV Address
    if (data_server == None):
    #    1. Arguement
    #    2. Env Vars
        if (data_srv == None):
            data_srv = os.getenv("myhero_data_srv")
        if (data_srv != None):
            # Turn into function here..
            set_data_server(data_srv)
    # 3. Prompt
    #    1. Address
    if (data_server == None):
        get_data_server = raw_input("What is the data server address? ")
        # print "Input Data: " + str(get_data_server)
        data_server = get_data_server

    print "Data Server: " + data_server
    sys.stderr.write("Data Server: " + data_server + "\n")


    data_key = args.datakey
    # print "Arg Data Key: " + str(data_key)
    if (data_key == None):
        data_key = os.getenv("myhero_data_key")
        # print "Env Data Key: " + str(data_key)
        if (data_key == None):
            get_data_key = raw_input("What is the data server authentication key? ")
            # print "Input Data Key: " + str(get_data_key)
            data_key = get_data_key
    # print "Data Server Key: " + data_key
    sys.stderr.write("Data Server Key: " + data_key + "\n")

    app_key = args.appsecret
    # print "Arg App Key: " + str(app_key)
    if (app_key == None):
        app_key = os.getenv("myhero_app_key")
        # print "Env Data Key: " + str(app_key)
        if (app_key == None):
            get_app_key = raw_input("What is the app server authentication key? ")
            # print "Input Data Key: " + str(get_app_key)
            app_key = get_app_key
    # print "App Server Key: " + app_key
    sys.stderr.write("App Server Key: " + app_key + "\n")

    # The API Service can run in two modes, direct or queue
    # In direct mode votes are sent direct to the data server
    # In queue mode votes are published to an MQTT server
    # Default mode is direct
    mode = args.mode
    if mode == None:
        mode = os.getenv("myhero_app_mode")
        if mode == None: mode = "direct"
    sys.stderr.write("App Server Server Mode is: " + mode + "\n")
    if mode == "queue":
        # To find the MQTT Server, two options are possible
        # In order of priority
        # 1.  Explicitly Set mqtthost and mqttport details from Arguments or Environment Variables
        # 2.  Leveraging DNS to lookup an SRV Record to get HOST IP and PORT information
        # Try #1 Option for Explicitly Set Options
        mqtt_host = args.mqtthost
        mqtt_port = args.mqttport
        if (mqtt_host == None and mqtt_port == None):
            mqtt_host = os.getenv("myhero_mqtt_host")
            mqtt_port = os.getenv("myhero_mqtt_port")
            if (mqtt_host == None and mqtt_port == None):
                # Move onto #2 and Try DNS Lookup
                mqtt_server = args.mqttserver
                if (mqtt_server == None):
                    mqtt_server = os.getenv("myhero_mqtt_server")
                    if (mqtt_server == None):
                        mqtt_server = raw_input("What is the MQTT Server FQDN for an SRV Lookup? ")
                sys.stderr.write("MQTT Server: " + mqtt_server + "\n")

                # Function to set the MQTT Server
                set_mqtt_server(mqtt_server)

    app.run(debug=True, host='0.0.0.0', port=listen)
