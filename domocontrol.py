#!/usr/bin/python
import time
import smbus
from db import Database
import datetime
#~ import threading

class Domocontrol:
    """Class DomoControl"""
    Z = {}
    
    def __init__(self, p='', ss='start'): #p = program dictionary
        self.p = p
        self.ss=ss
        self.i2c = 0 #(dev/i2c_x) Default is 0 but setBus check for right value       
        self.db = Database()
        self.mapping = {0:0, 1:1, 2:2, 3:4, 4:8, 5:16, 6:32, 7:64, 8:128}
        self.setBus()
        #~ print "*** Show device in /etc/i2c-%s" %self.i2c
        self.P = {} #Dict with Program
        self.Q = {} #Copy of Program
        self.A = {} #All other db information

    def setWebStatus(self): #Set all Status informations into Z Dict
        self.setup()
        self.Z = self.P

    def setZ(self,P):
        self.Z = P

    def now(self):
        return datetime.datetime.now()
 
    def setBus(self):
        self.device=[]
        for a in range(0,10):
            #~ print a
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
    
    def IOStatus(self, rw, board_address, io_address, value=0): #set / get IO Status: rw=read/write
        bus = smbus.SMBus(self.i2c)
        #~ bus.write_byte(int(var[0]['board_address']), 0xff)
        IOvalue = bus.read_byte(int(board_address))
        
        #~ print "Board_address:%s  IOValue:%s" %(board_address, IOvalue)
        if rw == 'read': #read bit value
            #~ print bin(value) #IO status
            bit_value = (IOvalue >> (int(io_address)-1))&1
            #~ print "Board_address:%s, io_address:%s, Value:%s" %(board_address, io_address, bit_value)

            return bit_value
        
        elif rw == 'write': #set bit value
            if value == 1:
                pass
                val = int(IOvalue) | self.mapping[ int(io_address) ]
                
                bus.write_byte(int(board_address), val)
            else:
                pass
                val = int(IOvalue) & (  0xffff - self.mapping[ int(io_address) ] )
                bus.write_byte(int(board_address), val)
            #~ print 
            #~ print "StatusPrec:%s,  bit:%s,  value:%s,  statusNew:%s" %(bin(IOvalue), address[0]['io_address'], value, bin(val) )
    
    

    def setup(self): #program setup
        q = 'SELECT id, in_id, delay, inverted, out_id, type_id, name, description, timer, chrono FROM program WHERE enable=1'
        res = self.db.query(q)
        for r in res:        
            self.P[r['id']] = r
            self.P[r['id']].update({'IN':r['inverted'], 'TIMER':0})
        
        #Area informations
        q = 'SELECT id, name, description FROM area'
        res = self.db.query(q)
        self.A['area']={}
        for r in res:
            self.A['area'].update({r['id'] : r})
        
        #Board informations
        q = 'SELECT * FROM board'
        res = self.db.query(q)
        self.A['board']={}
        for r in res:
            self.A['board'].update({r['id'] : r})
        
        #Board_io informations
        q = 'SELECT * FROM board_io'
        res = self.db.query(q)
        self.A['board_io']={}
        for r in res:
            self.A['board_io'].update({r['id'] : r})
     
        #Board_type informations
        q = 'SELECT * FROM board_type'
        res = self.db.query(q)
        self.A['board_type']={}
        for r in res:
            self.A['board_type'].update({r['id'] : r})
        
        #~ print self.P
        
        
    def resetIO(self): #To rese all port to begin and to end program
        q = 'SELECT io.board_id, io.address as io_address, io.io_type_id, b.board_type, b.address as board_address FROM board_io io, board b WHERE io.board_id=b.id'
        res = db.query(q)
        for r in res:       
            if r['io_type_id'] == 1 and int(r['board_address']) > 0: #input type
                print "INPUT  type %s" %r
                d.IOStatus('read', r['board_address'], r['io_address'], 1 )
                
            elif r['io_type_id'] == 2 and int(r['board_address']) > 0: #output type
                print "OUTPUT type %s" %r
                d.IOStatus('write', r['board_address'], r['io_address'], 0 )

        
    def loop(self):
        #~ print "Loop %s" % self.now()
       
        self.setZ(self.P)
        for p in self.P:   
            
            if self.P[p]['type_id'] == 4: # 4 = Manual
                #~ print "Manual %s" %P[p]
                in_address = self.getAddress(self.P[p]['in_id'])
                out_address = self.getAddress(self.P[p]['out_id'])
                #~ print "get in/out addres %s" %now()
                #~ print in_address
                in_status = self.IOStatus('read', in_address[0]['board_address'], in_address[0]['io_address'])
                
                out_status = self.IOStatus('read', out_address[0]['board_address'], out_address[0]['io_address'])
                
                #~ print "in_status:%s,  out_status:%s" %(in_status, out_status)
                self.P[p]['IN'] = in_status
                self.P[p]['OUT'] = out_status
                if self.P[p]['inverted'] == 1 : #flag inverted
                    in_status = not in_status
                
                #~ print "address_board:%s  io_address:%s  in_status:%s  out_status:%s" %(out_address[0]['board_address'], out_address[0]['io_address'], in_status, out_status)
                self.IOStatus('write', out_address[0]['board_address'], out_address[0]['io_address'], in_status)
        
        #~ print self.P




