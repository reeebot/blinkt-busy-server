#!/usr/bin/env python

import json
import blinkt
import threading
from time import sleep
from datetime import datetime
from gpiozero import CPUTemperature

from flask import Flask, jsonify, make_response, request
from random import randint

blinkThread = None

#setup the blinkt! hat
blinkt.set_brightness(0.2)
blinkt.show()


app = Flask(__name__)


def switchOn() :
	red = randint(10, 255)
	green = randint(10, 255)
	blue = randint(10, 255)
	blinkThread = threading.Thread(target=setColor, args=(red, green, blue))
	blinkThread.do_run = True
	blinkThread.start()

def switchOff() :
	if blinkThread != None :
		blinkThread.do_run = False
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
	blinkThread = threading.Thread(target=setColor, args=(255, 0, 0))
	blinkThread.do_run = True
	blinkThread.start()
	return (jsonify())

@app.route('/api/available', methods=['GET'])
def apiBusy() :
	switchOff()
	blinkThread = threading.Thread(target=setColor, args=(0, 255, 0))
	blinkThread.do_run = True
	blinkThread.start()
	return (jsonify())

@app.route('/api/away', methods=['GET'])
def apiBusy() :
	switchOff()
	blinkThread = threading.Thread(target=setColor, args=(150, 150, 0))
	blinkThread.do_run = True
	blinkThread.start()
	return (jsonify())

@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=False)
