#! /usr/bin/python
 
import os
from gps import *
from time import *
import time
import threading
import thread
import subprocess
import requests
import json
from StringIO import StringIO
import RPi.GPIO as GPIO
from requests.auth import HTTPBasicAuth 
import math

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(24, GPIO.IN,pull_up_down=GPIO.PUD_UP)


gpsd = None 
address_string = None
last_coordinates = None
 
class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd 
    gpsd = gps(mode=WATCH_ENABLE) 
    self.current_value = None
    self.running = True 
 
  def run(self):
    global gpsd
    while gpsp.running:
      gpsd.next() 

def retrieve():
	global gpsd
	while True:
		print 'Latittude     ',gpsd.fix.latitude
		print 'Longitude     ',gpsd.fix.longitude
		if (math.isnan(gpsd.fix.latitude) or (gpsd.fix.latitude == 0.0 and gpsd.fix.longitude == 0.0)):
			print "No fix"
		else:
			last_coordinates['lat'] = gpsd.fix.latitude
			last_coordinates['long'] = gpsd.fix.longitude
		time.sleep(5)
 
def addr():
	global gpsd
	global address_string
	global last_coordinates
	gcp_key = '' 
	if((not math.isnan(gpsd.fix.latitude)) and (not(gpsd.fix.latitude == 0.0 and gpsd.fix.longitude == 0.0)) ):
		url = 'https://maps.googleapis.com/maps/api/geocode/json?latlng=' + str(gpsd.fix.latitude) + ',' + str(gpsd.fix.longitude) + '&key=' + gcp_key
	else:
		url = 'https://maps.googleapis.com/maps/api/geocode/json?latlng=' + str(last_coordinates['lat']) + ',' + str(last_coordinates['long']) + '&key=' + gcp_key
	print url
	res = requests.get(url)
	temp_io = StringIO(res.content)
	data_json = json.load(temp_io)
	address =  data_json['results'][0]['formatted_address']
	address_string = address.encode('ascii','ignore')
	print address_string

def speak_addr():
	global gpsd
	global address_string
	if((not math.isnan(gpsd.fix.latitude)) and (not(gpsd.fix.latitude == 0.0 and gpsd.fix.longitude == 0.0)) ):
		speak("Current location is " + address_string)
	else:
		speak("No GPS fix. Last known location is " + address_string)


def speak(message):
	subprocess.call("./tts.sh "+ message,shell=True)

def notif():
	global address_string
        loc = address_string
        headers = {"Accept":"application/json","Content-Type":"application/json","User-Agent":"pi"}
        pushbullet_key = ""   
        url = "https://api.pushbullet.com/v2"
        message = {"body":loc,"title":"Current Location Is","type":"note"}
        msg_json = json.dumps(message)
        if((not math.isnan(gpsd.fix.latitude)) and (not(gpsd.fix.latitude == 0.0 and gpsd.fix.longitude == 0.0)) ):
                speak("Current location has been sent")
        else:
                speak("No GPS fix. Sending lasst known location")
        reply = requests.request("POST",url+"/pushes",data=msg_json,headers=headers,auth=HTTPBasicAuth(key,""))


def press1():
	while True:
	   inputValue = GPIO.input(23)
	   if (inputValue == False):
	       print("Button 1 press ")
	       addr()
	       speak_addr()
	   time.sleep(0.3)

def press2():
        while True:
           inputValue = GPIO.input(24)
           if (inputValue == False):
               print("Button 2 press ")
               addr()
	       notif()
           time.sleep(0.3)



if __name__ == '__main__':
  os.system('clear')
  gpsp = GpsPoller() 
  with open('last_coordinate.txt','r') as ip :
    last_coordinates = json.load(ip)
  try:
    gpsp.start() 
    time.sleep(5)
    thread.start_new_thread(retrieve,())
    thread.start_new_thread(press1,())
    thread.start_new_thread(press2,())
    while True:
      pass
  except (KeyboardInterrupt, SystemExit):
    with open('last_coordinate.txt','w') as op:
      json.dump(last_coordinates,op)
    print "\nKilling Thread..."
    gpsp.running = False
    gpsp.join() 
  print "Done.\nExiting."
