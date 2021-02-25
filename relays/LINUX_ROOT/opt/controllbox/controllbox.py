#!/usr/bin/env python3
from flask import Flask, render_template, Response
import smbus
from camera_pi import Camera
import re
import socket
import os
import time
import random
import sys

bpm = 75 #used for clack_octet()

app = Flask(__name__)

try:
  bus = smbus.SMBus(1) #i2c via smbus
except:
  print ("SMBus(1) not found")

relay_state = 0xff #all off


def i2c_send(payload):
  try:
    bus.write_byte_data(0x20, 0x6, payload) #0x20 adress (canbe set via A0-A3 DIP on the relay board), 0x6 type (required value)
  except:
    print ("failed to i2c_send")

def get_relay_state_string(): # returns relay state in form of "Relay 1: OFF Relay 2: ON Relay 3: OFF Relay 4: ON"
  global relay_state
  retval = ""
  for x in range(0, 4):
    retval += "Relay " + str(x+1) + ": "
    if relay_state & (1 << x): #if x-th bit is set relay is off
      retval += "OFF "
    else:
      retval += "ON "
  return retval

def get_IP(interface="eth0"): #returns the ip adress
  stream = os.popen('ip address show dev %s' %interface)
  output = stream.read()
  match = re.search("inet (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", output)
  IP = "0.0.0.0"
  if match is not None:
    IP = match[1]
  return IP

def clack_octet(octet): #signal an octet by allowing user to count the clacking the relay
  global relay_state
  padded_octet = octet.rjust(3, '0') #padding with zeroes from left to 3 characters
  pause_time = 60 / bpm
  for position in range(1,4):
    relay_index = random.randint(0, 3) #basic wearleveling
    for x in range(1,position+1): #count for position
      relay_state = relay_state ^ (1 << relay_index) #toggles the relay-index-th bit
      i2c_send(relay_state)
      time.sleep(pause_time)
    time.sleep(2*pause_time)
    number_at_current_position = ord(padded_octet[position-1]) - 48 #-48 converts ascii value to int value
    for x in range(1,number_at_current_position+1): #count for value
      relay_state = relay_state ^ (1 << relay_index) #toggles the relay-index-th bit
      i2c_send(relay_state)
      time.sleep(pause_time)
    time.sleep(2*pause_time)

def get_MAC(interface='eth0'): #returns the MAC adress
  try:
    str = open('/sys/class/net/%s/address' %interface).read().upper()
  except:
    str = "00:00:00:00:00:00"
  return str[0:17]

def gen(camera): #constantly pushes the current camera frame to the browser
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/') #landing page
def index():
	templateData = {
		'RELAY' : get_relay_state_string(),
		'IP' : get_IP(),
		'MAC' : get_MAC(),
	}
	return render_template('index.html', **templateData)

@app.route('/video_feed') #endpoint for the current frame
def video_feed():
    return #comment out to enable the camera
    return Response(gen(Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/<devicename>/<action>") # endpoint for controll actions
def action(devicename, action):
	global relay_state
	if re.match("^SW[1-4]$", devicename) is not None:
		switchid = ord(devicename[2]) - 48 - 1 #[2] is 0-4 (checked by regex), a numbers ASCII -48 is its value in int, -1 as the internal relay count is 0-3
		if action == "ON":
			relay_state &= ~(0x1 << switchid) # this sets the respective bit to 0
		if action == "OFF":
			relay_state |= (0x1 << switchid) # this sets the respective bit to 1

	i2c_send(relay_state)

	templateData = {
	  	'RELAY' : get_relay_state_string(),
		'IP' : get_IP(),
		'MAC' : get_MAC(),
	}

	return render_template('index.html', **templateData)

if __name__ == '__main__':
  IP = get_IP()
  last_octet = IP.split('.')[3]
  clack_octet(last_octet)
  time.sleep(2)
  i2c_send(0xff) # initial reset, all off
  relay_state = 0xff
  app.run(host='0.0.0.0', port=80, debug=False, threaded=True) #start the webserver

