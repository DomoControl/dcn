#!/usr/bin/python
import time
import smbus
from db import Database
import threading

class Domocontrol:
    """Class DomoControl"""
    
    def __init__(self, p='', ss='start'): #p = program dictionary
        self.p = p
        self.ss=ss
        self.db = Database()
        
    def loop(self):
        print "loop"
        

       
        t = threading.Timer(1, self.loop) #recall loop function every 1 second    
        if(self.ss == 'start'):
            t.start()
        else:
            t.cancel()

    def setBus(self):
        self.device=[]
        for a in range(0,10):
            try:
                i2c = smbus.SMBus(a)
                self.i2c = a #address i2c /dev/i2c_x
                for b in range(1,100):
                    try: 
                        #~ i2c.read_byte_data(b,0)
                        #~ self.device.append({a : b})
                        pass
                    except: 
                        pass
            except:
                pass
        
    def getAddress(self,id): #return io_address, board_address. id = program.in_id or program.out_id
        q = 'SELECT io.address io_address, b.address board_address  FROM board_io io, board b WHERE io.board_id=b.id AND io.id=%i' %id
        self.address = self.db.query(q)
        return self.address
    
    def IOStatus(self, IO, address, value=0): #set / get IO Status: IO=read/write, address:board_address+io_address, value:bit value
        bus = smbus.SMBus(self.i2c)
        #~ bus.write_byte(int(var[0]['board_address']), 0xff)
        IOvalue = bus.read_byte(int(address[0]['board_address']))
        if IO == 'read': #read bit value
            #~ print bin(value) #IO status
            bit_value = (IOvalue >> (int(address[0]['io_address'])-1))&1
            return bit_value
        
        elif IO == 'write': #set bit value
            pass
            if value == 1:
                pass
                val = int(IOvalue) | int(address[0]['io_address'] )
                bus.write_byte(int(address[0]['board_address']), val)
            else:
                pass 
                val = int(IOvalue) & int(value)
                bus.write_byte(int(address[0]['board_address']), val)
            #~ print IO, address, value, IOvalue
    
    def getProgram(self):
        print self.p
        return self.p

    def setProgram(self):
        if self.p['type_id'] == 1: #Timer
            self.setTimer()
        elif  self.p['type_id'] == 2: #TimerOut
            self.setTimeout()
        elif  self.p['type_id'] == 3: #Automatic
            self.setAutomatic()
        elif  self.p['type_id'] == 4: #Manual
            self.setManual()
            
    def setTimer(self):
        print "Timer"
        
    def setTimerOut(self): 
        print "TimerOut"
    
    def setAutomatic(self):
        print "Automatic"

    def setManual(self):
        #~ print "Manual"
        in_address = self.getAddress(self.p['in_id'])
        in_status = self.IOStatus('read',in_address)
        out_address = self.getAddress(self.p['out_id'])
        out_status = self.IOStatus('read',out_address)
        print in_status, out_status
        if out_status != in_status:
            self.IOStatus('write', out_address, in_status)
            pass
        #~ print in_address, out_address
        #~ print in_status, out_status
        
        
        
        


