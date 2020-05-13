#!/usr/bin/env python

import json
import blinkt, os
from time import sleep
from datetime import datetime
from gpiozero import CPUTemperature

from flask import Flask, jsonify, make_response, request, redirect, url_for, send_from_directory, render_template
from random import randint

#setup the blinkt! hat
blinkt.set_clear_on_exit(True)
blinkt.set_brightness(0.2)
blinkt.show()


app = Flask(__name__)


def setColor(r, g, b) :
	blinkt.set_all(r, g, b)
	blinkt.show()

def switchOff() :
	blinkt.clear()
	blinkt.show()

def getColor() :
	status = blinkt.get_pixel(0)
	return status


# API Initialization
@app.route('/')
def root():
    return render_template("index.html")     #app.send_static_file('index.html')

@app.route('/off', methods=['POST'])
def apiOff() :
	switchOff()
	return render_template("index.html", off="off")

@app.route('/busy', methods=['POST'])
def apiBusy() :
	switchOff()
	blinkt.set_all(255, 0, 0)
	blinkt.show()
	return render_template("index.html", busy="busy")

@app.route('/available', methods=['POST'])
def apiAvailable() :
	switchOff()
	blinkt.set_all(0, 255, 0)
	blinkt.show()
	return render_template("index.html", available="available")

@app.route('/away', methods=['POST'])
def apiAway() :
	switchOff()
	blinkt.set_all(0, 0, 255)
	blinkt.show()
	return render_template("index.html", away="away") #redirect('/')

@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=False)
