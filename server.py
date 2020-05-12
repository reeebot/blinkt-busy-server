#!/usr/bin/env python

import json
import blinkt
from time import sleep
from datetime import datetime
from gpiozero import CPUTemperature

from flask import Flask, jsonify, make_response, request
from random import randint

#setup the blinkt! hat
blinkt.set_clear_on_exit(False)
blinkt.set_brightness(0.2)
blinkt.show()


app = Flask(__name__)

def setColor(r, g, b) :
	blinkt.set_all(r, g, b)
	blinkt.show()

def switchOn() :
	r = randint(10, 255)
	g = randint(10, 255)
	b = randint(10, 255)
	blinkt.set_all(r, g, b)
	blinkt.show()

def switchOff() :
	blinkt.clear()
	blinkt.show()

# API Initialization
@app.route('/api/on', methods=['GET'])
def apiOn() :
	switchOff()
	switchOn()
	return jsonify({})

@app.route('/api/off', methods=['GET'])
def apiOff() :
	switchOff()
	return jsonify({})

@app.route('/api/busy', methods=['GET'])
def apiBusy() :
	switchOff()
	blinkt.set_all(255, 0, 0)
	blinkt.show()
	return (jsonify())

@app.route('/api/available', methods=['GET'])
def apiAvailable() :
	switchOff()
	blinkt.set_all(0, 255, 0)
	blinkt.show()
	return (jsonify())

@app.route('/api/away', methods=['GET'])
def apiAway() :
	switchOff()
	blinkt.set_all(140, 160, 0)
	blinkt.show()
	return (jsonify())

@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=False)
