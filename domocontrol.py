#!/usr/bin/python
import time
import smbus
from db import Database
import datetime
import sht21

class Domocontrol:
    """Class DomoControl"""

    def __init__(self):  # p = program dictionary
        self.i2c = 0  # (dev/i2c_x) Default is 0 but setBus check for right value
        self.db = Database()
        self.mapping = [0, 1, 2, 4, 8, 16, 32, 64, 128]
        self.setBus()
        # print "*** Show device in /etc/i2c-%s" %self.i2c
        self.P = {}  # Dict with Program
        self.Q = {}  # Copy of Program
        self.A = {}  # All other db information

    def setWebStatus(self):  # Set all Status informations into Z Dict
        self.setup()
        self.Z = self.P

    def now(self):
        return datetime.datetime.now()

    def setBus(self):
        print("Start setBus")
        self.device = []
        for a in range(0, 10):
            # print a
            try:
                i2c = smbus.SMBus(a)
                self.i2c = a  # address i2c /dev/i2c_x
                print('Device i2c: {}'.format(self.i2c))
                for b in range(1, 100):
                    try:
                        # i2c.read_byte_data(b,0)
                        # self.device.append({a : b})
                        pass
                    except:
                        pass
            except:
                pass

    def setup(self):  # program setup
        print("Start Domocontrol Setup")
        q = 'SELECT id, in_id, delay, inverted, out_id, type_id, name, description, timer, chrono FROM program WHERE enable=1'
        res = self.db.query(q)
        self.P = {}
        for r in res:
            self.P[r['id']] = r
            self.P[r['id']].update({'IN': r['inverted'], 'OUT': 0})

        # Area informations
        q = 'SELECT id, name, description FROM area'
        res = self.db.query(q)
        self.A['area'] = {}
        for r in res:
            self.A['area'].update({r['id']: r})

        # Board informations
        q = 'SELECT * FROM board'
        res = self.db.query(q)
        self.A['board'] = {}
        for r in res:
            self.A['board'].update({r['id']: r})

        # Board_io informations
        q = 'SELECT * FROM board_io'
        res = self.db.query(q)
        self.A['board_io'] = {}
        for r in res:
            self.A['board_io'].update({r['id']: r})

        # Board_type informations
        q = 'SELECT * FROM board_type'
        res = self.db.query(q)
        self.A['board_type'] = {}
        for r in res:
            self.A['board_type'].update({r['id']: r})
        # Program_type informations
        q = 'SELECT * FROM program_type'
        res = self.db.query(q)
        self.A['program_type'] = {}
        for r in res:
            self.A['program_type'].update({r['id']: r})
        print("End Domocontrol Setup")

    def resetIO(self):  # To rese all port to begin and to end program
        q = 'SELECT io.board_id, io.address as io_address, io.io_type_id, b.board_type_id, b.address as board_address FROM board_io io, board b WHERE io.board_id=b.id'
        res = db.query(q)
        for r in res:
            if r['io_type_id'] == 1 and int(r['board_address']) > 0:  # input type
                # print "INPUT  type %s" %r
                d.IOStatus('read', r['board_address'], r['io_address'], 1)
            elif r['io_type_id'] == 2 and int(r['board_address']) > 0:  # output type
                # print "OUTPUT type %s" %r
                d.IOStatus('write', r['board_address'], r['io_address'], 0)

    def getAddress(self, IO, id):  # return io_address, board_address. IO = in_id | out_id, id = Program ID
        io_id = self.P[id][IO]
        io_address = self.A['board_io'][io_id]['address']
        board_id = self.A['board_io'][io_id]['board_id']
        board_address = self.A['board'][board_id]['address']
        board_type_id = self.A['board'][board_id]['board_type_id']
        ret = {'program_id': id, 'io_address': io_address, 'board_address': board_address, 'board_type_id': board_type_id, 'IO': IO}
        # print ret
        return ret

    def IOStatus(self, data):  # get I/O Status
        # print rw, data, value
        if int(data['board_type_id']) == 1:  # i2c board
            bus = smbus.SMBus(self.i2c)
            IOvalue = bus.read_byte(int(data['board_address']))
            bit_value = (IOvalue >> (int(data['io_address'])-1)) & 1
            return bit_value
        elif int(data['board_type_id']) == 2:  # RS485 board
            pass  # To Do

        elif int(data['board_type_id']) == 3:  # WEB - virtual board
            return self.P[data['program_id']]['IN']

    def setIO(self, data, value):  # Set I/O status
        #~ print data, value
        if int(data['board_type_id']) == 1:  # I2C board
            bus = smbus.SMBus(self.i2c)
            IOvalue = bus.read_byte(int(data['board_address']))
            self.P[data['program_id']]['OUT'] = value
            if int(value) == 1:
                val = int(IOvalue) | self.mapping[int(data['io_address'])]
                bus.write_byte(int(data['board_address']), val)
            else:
                val = int(IOvalue) & (0xffff - self.mapping[int(data['io_address'])])
                bus.write_byte(int(data['board_address']), val)

        elif int(data['board_type_id']) == 3:  # Web board
            self.P[data['program_id']]['OUT'] = value

    def setIN(self, id, mode):
        self.P[int(id)]['IN'] = mode

    def getDict(self, dictionary):
        if dictionary == 'P':
            return self.P
        elif dictionary == 'A':
            return self.A

    def setDict(self, dictionary):
        if dictionary == 'P':
            self.P = dictionary
        elif dictionary == 'A':
            self.A = dictionary


    def loop(self):
        for p in self.P:  # p = id of self.P
            #print self.P
            if self.P[p]['type_id'] == 4:  # 4 = Manual
                in_address = self.getAddress('in_id', p)
                out_address = self.getAddress('out_id', p)
                in_status = self.IOStatus(in_address)
                self.P[p]['IN'] = in_status
                in_stat = 0 if int(self.P[p]['inverted']) == int(self.P[p]['IN']) else 1  # Status inverted is flag inverted = 1
                self.setIO(out_address, in_stat)

            elif self.P[p]['type_id'] == 1:  # 1 = Timer (luci scale)
                in_address = self.getAddress('in_id', p)
                out_address = self.getAddress('out_id', p)
                in_status = self.IOStatus(in_address)
                self.P[p]['IN'] = in_status

                if int(in_status) == 1:
                    timer = self.P[p]['timer'].split('-')
                    timer = (int(timer[0]) * 24 * 3600) + (int(timer[1]) * 3600) + (int(timer[2]) * 60) + int(timer[3])
                    if 'TIMER' in self.P[p]:
                        self.P[p].update({'TIMER': timer})
                    else:
                        self.P[p]['TIMER'] = timer
                    self.setIO(out_address, not int(self.P[p]['inverted']))

                if 'TIMER' in self.P[p] and int(self.P[p]['TIMER']) > 0:
                    self.P[p]['TIMER'] = int(self.P[p]['TIMER']) - 1
                else:
                    if 'TIMER' in self.P[p]:
                        del self.P[p]['TIMER']
                    self.setIO(out_address, int(self.P[p]['inverted']))

            elif self.P[p]['type_id'] == 2:  # 2 = Timeout (Pompa irrigazione)
                in_address = self.getAddress('in_id', p)
                out_address = self.getAddress('out_id', p)
                in_status = self.IOStatus(in_address)
                self.P[p]['IN'] = in_status

                if int(self.P[p]['IN']) == 1:
                    if 'TIMER' in self.P[p]:
                        if int(self.P[p]['TIMER']) > 0:
                            self.P[p]['TIMER'] = int(self.P[p]['TIMER']) - 1
                            self.setIO(out_address, (not int(self.P[p]['inverted'])))
                        else:
                            self.setIO(out_address, int(self.P[p]['inverted']))
                    else:
                        timer = self.P[p]['timer'].split('-')
                        timer = (int(timer[0]) * 24 * 3600) + (int(timer[1]) * 3600) + (int(timer[2]) * 60) + int(timer[3])
                        self.P[p].update({'TIMER': timer})
                else:
                    if 'TIMER' in self.P[p]:
                        del self.P[p]['TIMER']
                    self.setIO(out_address, int(self.P[p]['inverted']))


            elif self.P[p]['type_id'] == 3:  # 3 = Automatic
                in_address = self.getAddress('in_id', p)
                out_address = self.getAddress('out_id', p)
                in_status = self.IOStatus(in_address)
                self.P[p]['IN'] = in_status

                date = self.now().strftime('%Y-%m-%d')
                chrono = self.P[p]['chrono'].split(';')
                chronoOpen = 0
                for ch in chrono:
                    c = ch.split('-')
                    fd = c.pop(0)
                    fh = c.pop(0)
                    fm = c.pop(0)
                    fs = c.pop(0)

                    td = c.pop(0)
                    th = c.pop(0)
                    tm = c.pop(0)
                    ts = c.pop(0)

                    tfrom = '{} {}:{}:{}'.format(date, fh, fm, fs)
                    tto = '{} {}:{}:{}'.format(date, th, tm, ts)

                    FMT = '%Y-%m-%d %H:%M:%S'

                    timefrom = datetime.datetime.strptime(tfrom, FMT)
                    timeto = datetime.datetime.strptime(tto, FMT)

                    daynow = self.now().weekday() #Day of week

                    if (int(fd) == 7 and int(td) == 7 and self.now() > timefrom and self.now() < timeto) or (int(daynow) >= int(fd) and int(daynow) <= int(td) and self.now() > timefrom and self.now() < timeto):
                        chronoOpen = 1

                in_stat = 0 if int(self.P[p]['inverted']) == chronoOpen else 1  # Status inverted is flag inverted = 1
                self.setIO(out_address, in_stat)
        
        #look in there are temperature sensor
        try:
            tdiff = self.now() - self.tnow
            if tdiff.total_seconds() > 432: #Get data every 5 minutes
                self.tnow = self.now()
                for t in self.A['board']: 
                    if self.A['board'][t]['board_type_id'] == 4:
                        q = 'INSERT INTO sensor (type, value) VALUES("{}", "{}");'.format('1', round(sht21.SHT21(self.i2c).read_temperature(),1) )
                        print q
                        self.db.query(q)
                        q = 'INSERT INTO sensor (type, value) VALUES("{}", "{}");'.format('2', round(sht21.SHT21(self.i2c).read_humidity(),1) )
                        self.db.query(q)
                        print q
                        
        except:
            self.tnow = self.now() #crea la variabile self.tnow se non esiste
            
        
        
                
            


