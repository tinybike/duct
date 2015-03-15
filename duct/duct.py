#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
duct: a pyethereum ui

(c) Jack Peterson (jack@tinybike.net), 3/14/15

"""
from __future__ import division
from gevent import monkey
monkey.patch_all()
import sys
try:
    import cdecimal
    sys.modules["decimal"] = cdecimal
except:
    pass
import random
import base64
import string
import json
from decimal import *
import bcrypt
from flask import Flask, session, request, escape, url_for, redirect, render_template, send_from_directory
from flask.ext.socketio import SocketIO, emit
from werkzeug.datastructures import CallbackDict
from werkzeug import secure_filename
from pprint import pprint
import numpy as np
import pandas as pd
try:
    from colorama import Fore, Style, init
except ImportError:
    pass
from pyethereum import tester as t

np.set_printoptions(linewidth=225,
                    suppress=True,
                    formatter={"float": "{: 0.6f}".format})

pd.set_option("display.max_rows", 25)
pd.set_option("display.width", 1000)
pd.set_option('display.float_format', lambda x: '%.8f' % x)

# colorama
init()

app = Flask(__name__)
app.config["SECRET_KEY"] = "AOgQciQ7LyXRfnlYwGfeL"
app.config["DEBUG"] = True
app.config["TESTING"] = False
socketio = SocketIO(app)

#############
# Test data #
#############

max_iterations = 5
reports = np.array([[ 1,  1, -1, -1, 233, 16027.59],
                    [ 1, -1, -1, -1, 199,     0.  ],
                    [ 1,  1, -1, -1, 233, 16027.59],
                    [ 1,  1,  1, -1, 250,     0.  ],
                    [-1, -1,  1,  1, 435,  8001.00],
                    [-1, -1,  1,  1, 435, 19999.00]])
reputation = [1, 1, 1, 1, 1, 1]
scaled = [0, 0, 0, 0, 1, 1]
scaled_max = [1, 1, 1, 1, 435, 20000]
scaled_min = [-1, -1, -1, -1, 0, 8000]

#############
# Endpoints #
#############

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html", **locals())

@socketio.on('sync', namespace='/socket.io/')
def sync():
    print("client/server sync")
    emit('synced', { "data": "ok" })

############
# Ethereum #
############

def BR(string): # bright red
    return "\033[1;31m" + str(string) + "\033[0m"

def BB(string): # bright blue
    return Fore.BLUE + Style.BRIGHT + str(string) + Style.RESET_ALL

def BW(string): # bright white
    return Fore.WHITE + Style.BRIGHT + str(string) + Style.RESET_ALL

def BG(string): # bright green
    return Fore.GREEN + Style.BRIGHT + str(string) + Style.RESET_ALL

def blocky(*strings, **kwds):
    colored = kwds.get("colored", True)
    width = kwds.get("width", 108)
    bound = width*"#"
    fmt = "#{:^%d}#" % (width - 2)
    lines = [bound]
    for string in strings:
        lines.append(fmt.format(string))
    lines.append(bound)
    lines = "\n".join(lines)
    if colored:
        lines = BR(lines)
    return lines

def fix(x):
    return int(x * 0x10000000000000000)

def unfix(x):
    return x / 0x10000000000000000

@socketio.on("run-contract", namespace="/socket.io/")
def run_contract(req):
    print "run-contract:", json.dumps(req, indent=3, sort_keys=True)

    print BR("Forming new test genesis block")
    s = t.state()
    t.gas_limit = 100000000
    s = t.state()
    filename = "static/contracts/consensus.se"
    print BB("Testing contract:"), BG(filename)
    c = s.abi_contract(filename, gas=req['gas_input']) # 70000000
    
    num_players = len(reputation)
    num_events = len(reports[0])
    v_size = num_players * num_events

    reputation_fixed = map(fix, reputation)
    reports_fixed = map(fix, reports.ravel())
    scaled_max_fixed = map(fix, scaled_max)
    scaled_min_fixed = map(fix, scaled_min)

    arglist = [reports_fixed, reputation_fixed, scaled, scaled_max_fixed, scaled_min_fixed]
    result = c.interpolate(*arglist)
    result = np.array(result)
    reports_filled = result[0:v_size].tolist()
    reports_mask = result[v_size:].tolist()

    # center and initiate multistep pca loading vector
    arglist = [reports_filled, reputation_fixed, scaled,
               scaled_max_fixed, scaled_min_fixed, max_iterations]
    result = c.center(*arglist)
    result = np.array(result)
    weighted_centered_data = result[0:v_size].tolist()
    loading_vector = result[v_size:].tolist()

    arglist = [loading_vector, weighted_centered_data, reputation_fixed, num_players, num_events]
    while loading_vector[num_events] > 0:
        loading_vector = c.pca_loadings(*arglist)
        arglist[0] = loading_vector

    arglist = [loading_vector, weighted_centered_data, num_players, num_events]
    scores = c.pca_scores(*arglist)

    arglist = [scores, num_players, num_events]
    result = c.calibrate_sets(*arglist)
    result = np.array(result)
    set1 = result[0:num_players].tolist()
    set2 = result[num_players:].tolist()

    arglist = [set1, set2, reputation_fixed, reports_filled, num_players, num_events]
    result = c.calibrate_wsets(*arglist)
    result = np.array(result)
    old = result[0:num_events].tolist()
    new1 = result[num_events:(2*num_events)].tolist()
    new2 = result[(2*num_events):].tolist()

    arglist = [old, new1, new2, set1, set2, scores, num_players, num_events]
    adjusted_scores = c.pca_adjust(*arglist)

    arglist = [adjusted_scores, reputation_fixed, num_players, num_events]
    smooth_rep = c.smooth(*arglist)

    arglist = [smooth_rep, reports_filled, scaled, scaled_max_fixed,
               scaled_min_fixed, num_players, num_events]
    result = c.consensus(*arglist)

    result = np.array(result)
    outcomes_final = result[0:num_events].tolist()
    consensus_reward = result[num_events:].tolist()

    arglist = [outcomes_final, consensus_reward, smooth_rep, reports_mask, num_players, num_events]
    reporter_bonus = c.participation(*arglist)

    emit("contract-output", {
        "reputation": map(unfix, smooth_rep),
        "outcomes": map(unfix, outcomes_final),
        "reporter_bonus": map(unfix, reporter_bonus),
    })

def main():
    if app.config['DEBUG']:
        socketio.run(app, port=9000)
    else:
        socketio.run(app, host='0.0.0.0', port=9090)

if __name__ == "__main__":
    main()
