#! /usr/bin/python
'''
    Web Service for Simple Superhero Voting Application

    This is the Web Service for a basic microservice demo application.
    The application was designed to provide a simple demo for Cisco Mantl
'''

from flask import Flask, render_template, request, jsonify
import datetime
import json
import os, sys
import requests

app = Flask(__name__)

@app.route("/")
def template_test():
    # Check for submitted vote
    vote = request.args.get('hero')
    if (vote):
        uv = app_server + "/vote/" + vote
        app_requests_headers = {"key": app_key}
        vpage = requests.post(uv, headers=app_requests_headers)

    u = app_server + "/options"
    app_requests_headers = {"key": app_key}
    page = requests.get(u, headers=app_requests_headers)
    options = page.json()
    hero_list = options["options"]

    return render_template('home.html', hero_list=hero_list, title="Microservice Demo Application", current_time=datetime.datetime.now())

@app.route("/about")
def about():
    return render_template('about.html', title="About", current_time=datetime.datetime.now())

@app.route("/results")
def results():
    # Check for submitted vote
    vote = request.args.get('hero')
    if (vote):
        uv = app_server + "/vote/" + vote
        app_requests_headers = {"key": app_key}
        vpage = requests.post(uv, headers=app_requests_headers)

    u = app_server + "/v2/results"
    app_requests_headers = {"key": app_key}
    page = requests.get(u, headers=app_requests_headers)
    # Display the timestamp of the results based on informaiton passed by the APP server
    try:
        timestamp = page.headers["data_timestamp"]
        timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
    except:
        timestamp = datetime.datetime.now()
    tally = page.json()
    return render_template('results.html', tally = tally, title="Results", current_time=timestamp)

@app.template_filter()
def datetimefilter(value, format='%Y/%m/%d %H:%M'):
    """convert a datetime to a different format."""
    return value.strftime(format)

app.jinja_env.filters['datetimefilter'] = datetimefilter

if __name__=='__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser("MyHero Web Service")
    parser.add_argument(
        "-a", "--app", help="Address of app server", required=False
    )
    parser.add_argument(
        "-k", "--appkey", help="App Server Authentication Key Used in API Calls", required=False
    )
    parser.add_argument(
        "--port", help="Port to listen on", required=False, default=5000
    )

    args = parser.parse_args()

    # Determine port number
    listen = int(args.port)
    print("Listen: " + str(listen))

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


    app.run(debug=True, host='0.0.0.0', port=listen)


