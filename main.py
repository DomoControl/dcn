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
        if x > 2: #Get Database status every tot cycle
            x = 0
            d.setup()
        
        #~ print "Stop %s" %now()
        #~ threading.Timer(1, loop).start()
        time.sleep(0.1)

        #~ print d.Z
loop() #start loop
