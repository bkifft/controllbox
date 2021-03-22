#!/usr/bin/env python3
from flask import Flask, render_template, Response
import smbus
# from camera_pi import Camera
import re
import socket
import os
import time
import random
import sys
import schedule
from threading import Thread

bpm = 75  # used for clack_octet()

app = Flask(__name__)

try:
    bus = smbus.SMBus(1)  # i2c via smbus
except:
    print("SMBus(1) not found")

relay_state = 0xff  # all off
relay_time = [0] * 4


def relay_send(payload):
    try:
        bus.write_byte_data(0x20, 0x6,
                            payload)  # 0x20 adress (canbe set via A0-A3 DIP on the relay board), 0x6 type (required value)
    except:
        print("failed to i2c_send")


def relay_loop():
    global relay_state
    global relay_time
    for i in range(len(relay_time)):
        if relay_time[i] > 0:
            relay_time[i] -= 1
            if relay_time[i] == 0:
                relay_state |= (0x1 << i)  # this sets the respective bit to 1, turning the relay off
                relay_send(relay_state)


def run_schedule():
    while 1:
        schedule.run_pending()
        time.sleep(0.01)


def get_relay_state_string():  # returns relay state in form of "Relay 1: OFF Relay 2: ON Relay 3: OFF Relay 4: ON"
    global relay_state
    retval = ""
    for x in range(0, 4):
        retval += "Relay " + str(x + 1) + ": "
        if relay_state & (1 << x):  # if x-th bit is set relay is off
            retval += "OFF "
        else:
            retval += "ON "
    return retval


def get_relay_time_string():  # returns relay times in form of "Relay 1: 1s Relay 2: 2s Relay 3: 3s Relay 4: 0s"
    global relay_state
    global relay_time
    retval = ""
    for x in range(0, 4):
        retval += "Relay " + str(x + 1) + ": " + str(relay_time[x]) + "s "
    return retval


def get_IP(interface="eth0"):  # returns the ip adress
    stream = os.popen('ip address show dev %s' % interface)
    output = stream.read()
    match = re.search("inet (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", output)
    IP = "0.0.0.0"
    if match is not None:
        IP = match[1]
    return IP


def clack_octet(octet):  # signal an octet by allowing user to count the clacking the relay
    return
    global relay_state
    padded_octet = octet.rjust(3, '0')  # padding with zeroes from left to 3 characters
    pause_time = 60 / bpm
    for position in range(1, 4):
        relay_index = random.randint(0, 3)  # basic wearleveling
        for x in range(1, position + 1):  # count for position
            relay_state = relay_state ^ (1 << relay_index)  # toggles the relay-index-th bit
            relay_send(relay_state)
            time.sleep(pause_time)
        time.sleep(2 * pause_time)
        number_at_current_position = ord(padded_octet[position - 1]) - 48  # -48 converts ascii value to int value
        for x in range(1, number_at_current_position + 1):  # count for value
            relay_state = relay_state ^ (1 << relay_index)  # toggles the relay-index-th bit
            relay_send(relay_state)
            time.sleep(pause_time)
        time.sleep(2 * pause_time)


def get_MAC(interface='eth0'):  # returns the MAC adress
    try:
        str = open('/sys/class/net/%s/address' % interface).read().upper()
    except:
        str = "00:00:00:00:00:00"
    return str[0:17]



def get_template_data():
    template_data = {
        'RELAY': get_relay_state_string(),
        'IP': get_IP(),
        'MAC': get_MAC(),
        'HOSTNAME': 'fixme',
        'TIME': get_relay_time_string(),
    }
    return template_data


@app.route('/')  # landing page
def index():
    template_data = get_template_data()
    return render_template('index.html', **template_data)


@app.route("/<devicename>/<action>")  # endpoint for controll actions
def action(devicename, action):
    global relay_state
    global relay_time
    if re.match("^SW[1-4]$", devicename) is not None:
        relay_id = ord(devicename[
                           2]) - 48 - 1  # [2] is 0-4 (checked by regex), a numbers ASCII -48 is its value in int, -1 as the internal relay count is 0-3
        if action == "ON":
            relay_state &= ~(0x1 << relay_id)  # this sets the respective bit to 0
            relay_time[relay_id] = 0
        if action == "OFF":
            relay_state |= (0x1 << relay_id)  # this sets the respective bit to 1
            relay_time[relay_id] = 0
        if action == "TOGGLE":
            relay_state ^= (0x1 << relay_id)  # this toggles the respective bit
            relay_time[relay_id] = 0
        if re.match("^\d*$", action) is not None:
            relay_state &= ~(0x1 << relay_id)  # this sets the respective bit to 0
            relay_time[relay_id] += int(action)

    relay_send(relay_state)

    return "<script>window.location.href = \"/\";</script>"
    


if __name__ == '__main__':
    schedule.every(1).seconds.do(relay_loop)
    t = Thread(target=run_schedule)
    t.start()
    IP = get_IP()
    last_octet = IP.split('.')[3]
    #  clack_octet(last_octet)
    time.sleep(2)
    relay_send(0xff)  # initial reset, all off
    relay_state = 0xff
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)  # start the webserver
