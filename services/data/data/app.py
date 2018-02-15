#! /usr/bin/python
'''
    Data Service for Simple Superhero Voting Application

    This is the Data Service for a basic microservice demo application.
    The application was designed to provide a simple demo for Cisco Mantl

'''
__author__ = 'hapresto'

from flask import Flask, make_response, request, jsonify, Response
import datetime, json, sys, os
from collections import Counter

app = Flask(__name__)
data_dir = "./"
data_file = data_dir + "heros.txt"

@app.route("/hero_list")
def hero_list():
    hero_list = []
    with open("heros.txt") as f:
        for line in f:
            line = line.rstrip()
            hero_list.append(line)
    resp = make_response(jsonify(heros=hero_list))
    return resp

@app.route("/vote/<hero>", methods=["GET", "POST"])
def vote(hero):
    if request.method == "GET":
        with open(data_dir + "votes.txt", "a") as f:
            f.write(hero + "\n")
        resp = make_response(jsonify(result="1"))
        return resp
    if request.method == "POST":
        # Verify that the request is propery authorized
        authz = valid_request_check(request)
        if not authz[0]:
            return authz[1]
        with open(data_dir + "votes.txt", "a") as f:
            f.write(hero + "\n")
        resp = make_response(jsonify(result="1"))
        return resp


@app.route("/results")
def results():
    tally = Counter()
    with open(data_dir + "votes.txt") as f:
        for line in f:
            line = line.rstrip()
            tally[line] += 1

    resp = make_response(jsonify(tally))

    return resp

@app.route("/v2/results")
def results_v2():
    tally = Counter()
    with open(data_dir + "votes.txt") as f:
        for line in f:
            line = line.rstrip()
            tally[line] += 1
    total_votes = float(sum(tally.values()))

    tally = sorted(tally.items(), key=lambda (k, v): v, reverse=True)

    for i, entry in enumerate(tally):
        # Add Percentage of votes as third element in entry
        tally[i] = list(tally[i])
        tally[i].append((entry[1]/total_votes)*100)

    tally = json.dumps(tally)

    resp = Response(
        tally,
        content_type='application/json',
        headers={"Total Votes": total_votes},
        status=200)
    return resp


@app.route("/options", methods=["GET", "PUT", "POST"])
def options_route():
    '''
    Methods used to view options, add new option, and replace options.
    '''
    authz = valid_request_check(request)
    if not authz[0]:
        return authz[1]

    if request.method == "GET":
        options = {"options":option_list()}
        status = 200
    if request.method == "PUT":
        try:
            data = request.get_json(force=True)
            # Verify data is of good format
            # { "option" : "Deadpool" }
            options = {"options": add_option(data["option"])}
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
            sys.stderr.write("New Options:" + str(data["options"]) + "\n")
            options = {"options":replace_options(data["options"])}
            status = 201

        except KeyError:
            error = {"Error": "API expects dictionary object with single element with key 'option' and value a list of options"}
            status = 400
            resp = Response(json.dumps(error), content_type='application/json', status=status)
            return resp

    resp = Response(
        json.dumps(options, sort_keys=True, indent = 4, separators = (',', ': ')),
        content_type='application/json',
        status=status)
    return resp

@app.route("/options/<option>", methods=["DELETE"])
def option_delete_route(option):
    '''
    Delete an option from the the option_list.
    '''
    authz = valid_request_check(request)
    if not authz[0]:
        return authz[1]

    if request.method == "DELETE":
        options = {"options": remove_option(option)}
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
        if request.headers["key"] == data_key:
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

def option_list():
    '''
    Get a list of possible options.
    '''
    options = []
    with open(data_file) as f:
        for line in f:
            line = line.rstrip()
            options.append(line)
    return options

def add_option(option):
    '''
    Add a new option to the list.
    '''
    options = option_list()
    if option.upper() in [o.upper() for o in options]:
        return "Option already in list."

    with open(data_file, "a") as f:
        f.write(option + "\n")

    return option_list()

def remove_option(option):
    '''
    Remove and option from the list.
    '''
    options = option_list()
    if option.upper() in [o.upper() for o in options]:
        options.remove(option)
        with open(data_file, "w") as f:
            f.write("\n".join(options) + "\n")
    return option_list()

def replace_options(options):
    '''
    Full replacement of option list
    '''
    with open(data_file, "w") as f:
        f.write("\n".join(options) + "\n")

    return option_list()

if __name__=='__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser("MyHero Data Service")
    parser.add_argument(
        "-s", "--datasecret", help="Data Server Key Expected in API Calls", required=False#, default="e009ae3c3b80e73c0c768561b077e82e"
    )
    parser.add_argument(
        "--datadir", help="Directory to use for Data", required=False
    )
    parser.add_argument(
        "--port", help="Port to listen on", required=False, default=5000
    )

    args = parser.parse_args()

    # Determine port number
    listen = int(args.port)
    print("Listen: " + str(listen))

    data_key = args.datasecret
    print "Arg Data Key: " + str(data_key)
    if (data_key == None):
        data_key = os.getenv("myhero_data_key")
        print "Env Data Key: " + str(data_key)
        if (data_key == None):
            get_data_key = raw_input("What is the data server authentication key? ")
            print "Input Data Key: " + str(get_data_key)
            data_key = get_data_key
    # print "Data Server Key: " + data_key
    sys.stderr.write("Data Server Key: " + data_key + "\n")

    arg_data_dir = args.datadir
    if (arg_data_dir == None):
        arg_data_dir = os.getenv("myhero_data_dir")
        if (arg_data_dir == None):
            print("Setting Data Directory to default")
            arg_data_dir = "./"

    # Check if data directory exists
    if (os.path.isdir(arg_data_dir)):
        # Director exists, use it
        print("Valid Data Directory Found.")
        data_dir = arg_data_dir
    else:
        print("Given Data Directory Invalid.  Using Default.")
    sys.stderr.write("Data Directory: " + data_dir + "\n")

    data_file = data_dir + "myhero_options.txt"

    # Check if Options File Exists
    if (not os.path.isfile(data_file)):
        #File doesn't exist, copy sample
        print("Options file missing, Creating default.  ")
        from shutil import copyfile
        copyfile("sample_heros.txt", data_file)

    app.run(debug=True, host='0.0.0.0', port=listen)

