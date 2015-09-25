#!/usr/bin/python
from db import Database
import threading
import time
import smbus
from date import now  # get time function

T=[] #lista di Thread in esecuzione
ValueInputs = {} #Dizionario con valire board_id: valore_ingressi

class readInputs(threading.Thread):
    global ValueInputs, T


    def __init__(self,board):
        threading.Thread.__init__(self)
        self.i2c = 0  # (dev/i2c_x) Default is 0 but getBusValue check for right value of BUS port I2C
        self.getBusValue()  # set /dev/i2c_x
        self.board = board  # Dizionario board


    def getBusValue(self):  # Controlla il numero del BUS device
        """
        Controlla il numero del divice I2C
        """
        print("Start getBusValue")
        self.device = []
        for a in range(0, 10):
            # print a
            try:
                i2c = smbus.SMBus(a)
                self.i2c = a  # address i2c /dev/i2c_x
                print('Device i2c: {}'.format(self.i2c))
            except:
                pass


    def valueInputs(self):  # ritorna il valore degli ingressi
        return ValueInputs


    def run(self):
        # print self.board
        if self.board['board_type_id'] == 1:
            # print "I2C"
            # print self.board['address']
            valIn = self.read_i2c(self.board['address'])
            ValueInputs.update({self.board['id']: valIn})  # scrive il valore degli ingesssi I2C sul dizionario
        elif self.board['board_type_id'] == 2:
            # print "RS485"
            pass
        elif self.board['board_type_id'] == 3:
            # print "WEB"
            pass
        elif self.board['board_type_id'] == 4:
            # print "SHT21"
            pass
        elif self.board['board_type_id'] == 5:
            # print "PD9535"
            pass
        T.remove(r['id']) #Rimuove il Thread dala lista dei Thread in quanto e' terminato


    def read_i2c(self, board_address):
        # print "Thread %s INIZIO" %board_address
        # time.sleep(10)
        # print "Thread %s FINE" %board_address
        bus = smbus.SMBus(self.i2c)
        data = bus.read_byte(board_address)  # legge lo stato degli ingressi
        # print data
        return data



db = Database()
q_board = "SELECT * FROM board WHERE enable=1"
r_board = db.query(q_board)

while True:
    for r in r_board:
        print "-" * 50
        timebegin = now()

        if r['id'] in T:
            pass
            # print r['id'], 'ESISTE'
        else:
            # print r['id'], 'NON ESISTE'
            T.append(r['id'])
            t = readInputs(r)
            t.start()

        print t.valueInputs()

        print now() - timebegin
        time.sleep(0.2)
