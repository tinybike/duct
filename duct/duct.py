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
import json
from decimal import *
import bcrypt
from flask import Flask, session, request, escape, url_for, redirect, render_template, send_from_directory
from flask.ext.socketio import SocketIO, emit
from werkzeug.datastructures import CallbackDict
from werkzeug import secure_filename
import numpy as np
import pandas as pd
from pyethereum import tester, utils, abi

np.set_printoptions(linewidth=225,
                    suppress=True,
                    formatter={"float": "{: 0.6f}".format})

pd.set_option("display.max_rows", 25)
pd.set_option("display.width", 1000)
pd.set_option('display.float_format', lambda x: '%.8f' % x)

app = Flask(__name__)
app.config["SECRET_KEY"] = "AOgQciQ7LyXRfnlYwGfeL"
app.config["DEBUG"] = True
app.config["TESTING"] = False
socketio = SocketIO(app)

print "Forming new test genesis block"
s = tester.state()
tester.gas_limit = 100000000
s = tester.state()

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

def fix(x):
    return int(x * 0x10000000000000000)

def unfix(x):
    return x / 0x10000000000000000

@socketio.on("create-contract", namespace="/socket.io/")
def create_contract(req):
    print "Compiling:"
    print req['source']
    c = s.abi_contract(req['source'], gas=req['gas_input'])
    print "contract address:", c.address
    c.__dict__.pop('_translator')
    emit('contract-created', {
        'address': c.__dict__.pop('address'),
        'functions': c.__dict__.keys(),
    })

@socketio.on("run-contract", namespace="/socket.io/")
def run_contract(req):
    print "run-contract:", json.dumps(req, indent=3, sort_keys=True)
    c = s.abi_contract(req['contract_address'], gas=req['gas_input'])
    output = c.main()
    emit("contract-output", { "output": output })

def main():
    if app.config['DEBUG']:
        socketio.run(app, port=9000)
    else:
        socketio.run(app, host='0.0.0.0', port=9090)

if __name__ == "__main__":
    main()
