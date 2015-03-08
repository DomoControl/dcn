#!/usr/bin/python
from time import sleep
import domocontrol

d = domocontrol.Domocontrol()
d.setup()

def loop():
    x = ''
    while True:
        d.loop()
        x = 1
        if x > 10: #Get Database status every tot cycle
            x = 0
            d.setup()

        sleep(1)
        

        #~ print d.P

if __name__ == '__main__':  
    loop()
    print("Fine")
