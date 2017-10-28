#!/bin/bash

stty -F /dev/ttyS0 9600
sudo gpsd /dev/ttyS0 -F /var/run/gpsd.sock
