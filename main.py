#!/usr/bin/python
import time
import smbus
from db import Database
import datetime
import domocontrol


d = domocontrol.Domocontrol()
d.setup()

def loop():
    x = 0
    while True:
        d.loop()
        
        x +=1
        if x > 10: #Get Database status every tot cycle
            x = 0
            d.setup()
        
        #~ print "Stop %s" %now()
        #~ threading.Timer(1, loop).start()
        time.sleep(1)

loop() #start loop
