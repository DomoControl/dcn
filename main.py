#!/usr/bin/python
import time
import smbus
from db import Database
import datetime
import domocontrol
import web

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

        time.sleep(1)
        

        #~ print d.P

if __name__ == '__main__':  
    loop()
    print "Fine"
