#!/usr/bin/python
import date
import time
import smbus
from db import Database
import datetime
import copy
import sht21
import os
import threading
OutChange = {}
A = {}
P = {}

class Domocontrol:
    """Class DomoControl"""

    def __init__(self):
        self.db = Database()
        self.i2c = 0
        self.getBusValue()
        self.P = {}
        self.A = {}
        self.IOThread = []
        self.t_board_n = ()
        self.t_board_id = ()
        self.t_board_type_id = ()
        self.t_board_address = ()
        self.t_board_type = ()
        self.t_board_io_address = ()
        self.t_board_io_id = ()
        self.l_board_io_val = []
        self.l_board_bin_val = []
        self.l_board_bin_onchange = []
        self.l_board_changerequest = []
        self.PThread = []
        self.dir_root = os.path.dirname(os.path.abspath(__file__))
        self.initialize()

    def getBusValue(self):
        """
        Controlla il numero del divice I2C
        """
        print 'Start getBusValue'
        self.device = []
        for a in range(0, 10):
            try:
                self.i2c = smbus.SMBus(a)
                self.i2c = a
                print 'Device i2c: {}'.format(self.i2c)
            except:
                pass

    def read_i2c(self, board_address):
        """
        Ritorna il valore in byte dei dispositivi I2C.
        """
        bus = smbus.SMBus(self.i2c)
        return bus.read_byte(board_address)

    def write_i2c(self, board_address, val):
        bus = smbus.SMBus(self.i2c)
        bus.write_byte(board_address, val)

    def runIO(self, board_id, board_type_id, board_n):
        """
        Si occupa di leggere e scrivere i valori degli IO
        """
        if board_type_id == 0:
            pass
        elif board_type_id == 1:
            val = self.read_i2c(self.t_board_address[board_n])
            self.l_board_bin_val[board_n] = val
            if self.l_board_changerequest[board_n] == 1:
                print 'Passa di qui', self.l_board_bin_onchange[self.t_board_n[board_id]], self.l_board_bin_val[board_n]
                self.l_board_bin_val[board_n] = self.l_board_bin_onchange[board_n]
                self.write_i2c(self.t_board_address[board_n], self.l_board_bin_val[board_n])
                self.l_board_changerequest[board_n] = self.l_board_bin_onchange[board_n] = 0
        elif board_type_id == 2:
            pass
        elif board_type_id == 3:
            if self.l_board_changerequest[board_n] == 1:
                self.l_board_bin_val[board_n] = self.l_board_bin_onchange[board_n]
                self.l_board_changerequest[board_n] = 0
        elif board_type_id == 4 or board_type_id == 6:
            temperature = round(sht21.SHT21(self.i2c).read_temperature(), 1)
            humidity = round(sht21.SHT21(self.i2c).read_humidity(), 1)
            self.l_board_bin_val[self.t_board_type_id.index(4)] = temperature
            self.l_board_bin_val[self.t_board_type_id.index(6)] = humidity
            time.sleep(1)
        elif board_type_id == 5:
            pass
        self.IOThread[self.t_board_id.index(board_id)] = 0
        print self.l_board_bin_val, self.l_board_changerequest, self.l_board_bin_onchange, board_id, board_type_id

    def InT(self, board_id, board_type, board_n):
        threading.Thread(target=self.runIO, args=(board_id, board_type, board_n)).start()

    def getIO(self):
        """
        LOOP si occupa di inizializzare il Thread per l'aggiornamento della lettura/scrittura IO
        """
        for bid in self.t_board_id:
            if self.IOThread[self.t_board_id.index(bid)] == 1:
                pass
            else:
                self.IOThread[self.t_board_id.index(bid)] = 1
                self.InT(bid, self.t_board_type_id[self.t_board_id.index(bid)], self.t_board_id.index(bid))

    def setProg(self):
        """
        LOOP si occupa del programma
        """
        for p in self.P:
            print p

    def setClickData(self, data):
        """
        Called from web.py when clicked into I/O
        board_n, address, In value
        """
        IO = 0 if data[2] else 1
        self.l_board_bin_onchange[self.t_board_n[data[0]]] = self.setBit(self.l_board_bin_val[self.t_board_n[data[0]]], data[1], IO)
        self.l_board_changerequest[self.t_board_n[data[0]]] = 1
        print 'Data:%s,  changerequest: %s,  board_bin_onchange:%s   IO:%s' % (data,
         self.l_board_changerequest,
         self.l_board_bin_onchange,
         IO)

    def now(self):
        """
        Ritorna l'ora corrente
        """
        return date.now()

    def initialize(self):
        """
        Funzione di setup
        Imposta il valore di tutti i dizionari per il corretto funzionamento
        """
        global A
        global P
        print 'Start Domocontrol Setup'
        q = 'SELECT * FROM board ORDER BY id'
        res = self.db.query(q)
        l_board_id = []
        l_board_type_id = []
        l_board_n = []
        l_board_address = []
        self.l_board_bin_val = []
        self.l_board_bin_onchange = []
        self.l_board_changerequest = []
        n = 0
        for r in res:
            l_board_n.append(n)
            l_board_id.append(r['id'])
            l_board_type_id.append(r['board_type_id'])
            n += 1
            l_board_address.append(r['address'])
            self.l_board_bin_val.append(0)
            self.l_board_bin_onchange.append(0)
            self.IOThread.append(0)
            self.l_board_changerequest.append(0)

        self.t_board_id = tuple(l_board_id)
        self.t_board_type_id = tuple(l_board_type_id)
        self.t_board_n = tuple(l_board_n)
        self.t_board_address = tuple(l_board_address)
        q = 'SELECT id, address, board_id FROM board_io ORDER BY board_id, address'
        res = self.db.query(q)
        l_board_io_address = []
        l_board_io_id = []
        l_board_io_val = []
        tmp_address = []
        tmp_id = []
        tmp_val = []
        self.t_board_io_address = ()
        self.l_board_io_id = ()
        for lb in self.t_board_id:
            for r in res:
                if r['board_id'] == lb:
                    tmp_address.append(r['address'])
                    tmp_id.append(r['id'])
                    tmp_val.append(0)

            l_board_io_address.append(tuple(tmp_address))
            l_board_io_id.append(tuple(tmp_id))
            self.l_board_io_val.append(tmp_val)
            tmp_address = []
            tmp_id = []
            tmp_val = []

        self.t_board_io_address = tuple(l_board_io_address)
        self.t_board_io_id = tuple(l_board_io_id)
        q = 'SELECT * FROM board_type ORDER BY id'
        res = self.db.query(q)
        l_board_type = []
        for r in res:
            l_board_type.append(r['id'])

        self.t_board_type = tuple(l_board_type)
        print 'self.t_board_n      :', self.t_board_n
        print 'self.t_board_id     :', self.t_board_id
        print 'self.t_board_type_id:', self.t_board_type_id
        print 'self.t_board_type   :', self.t_board_type
        print 'self.t_board_address:', self.t_board_io_address
        print 'self.t_board_io_id  :', self.t_board_io_id
        print 'self.l_board_io_val :', self.l_board_io_val
        q = 'SELECT * FROM board'
        res = self.db.query(q)
        self.A['board'] = {}
        for r in res:
            self.A['board'].update({r['id']: r})
            OutChange[r['id']] = {}

        q = 'SELECT * FROM board_io'
        res = self.db.query(q)
        self.A['board_io'] = {}
        for r in res:
            self.A['board_io'].update({r['id']: r})

        icon_path = os.path.join(self.dir_root, 'static/icon')
        files = [ fn for fn in os.listdir(icon_path) ]
        self.A['icon'] = files
        q = 'SELECT id, in_id, delay, inverted, out_id, type_id, name, description, timer, chrono, enable FROM program WHERE enable = 1'
        res = self.db.query(q)
        self.P = {}
        self.PThread = []
        for r in res:
            self.PThread.append(0)
            self.P.update({r['id']: r})
            self.P[r['id']].update({'TA': 0})

        q = 'SELECT id, name, description, sort FROM area ORDER BY sort'
        res = self.db.query(q)
        self.A['area'] = {}
        for r in res:
            self.A['area'].update({r['id']: r})

        q = 'SELECT a.id AS area_id, a.name AS area_name, a.description AS area_description,                 bio.id AS  board_io_id,  bio.io_type_id AS board_io_io_type_id, bio.name AS board_io_name, bio.description AS board_io_description, bio.address AS board_io_address,                   bio.board_id AS board_io_board_id, bio.icon_on AS board_io_icon_on, bio.icon_off AS board_io_icon_off             FROM board_io AS bio                 LEFT JOIN area AS a ON bio.area_id=a.id             ORDER BY a.sort'
        res = self.db.query(q)
        self.A['area_board_io'] = {}
        for r in res:
            self.A['area_board_io'].update({r['board_io_id']: r})

        q = 'SELECT id, type, name, description FROM io_type'
        res = self.db.query(q)
        self.A['io_type'] = {}
        for r in res:
            self.A['io_type'].update({r['id']: r})

        q = 'SELECT * FROM board_type'
        res = self.db.query(q)
        self.A['board_type'] = {}
        for r in res:
            self.A['board_type'].update({r['id']: r})

        q = 'SELECT * FROM program_type'
        res = self.db.query(q)
        self.A['program_type'] = {}
        for r in res:
            self.A['program_type'].update({r['id']: r})

        A = self.A
        P = self.P
        print 'End Domocontrol Setup'

    def getData(self, data):
        return eval(data)

    def loop(self):
        pass

    def getInStatus(self):
        """
        Get Byte Status of all board
        Legge il valore degli ingressi/uscite delle varie schede
        """
        for board_id in self.A['board']:
            board = self.A['board'][board_id]
            if int(board['board_type_id']) == 1:
                bus = smbus.SMBus(self.i2c)
                data = bus.read_byte(int(board['address']))
                data_old = self.IO['io'][board['id']]['value']
                if data != data_old:
                    diff = int(data) ^ int(data_old)
                    self.IO['io'].update({board['id']: {'value': data,
                                   'update': diff}})
            elif int(board['board_type_id']) == 2:
                self.IO['io'].update({board['id']: 0})
            elif int(board['board_type_id']) == 3:
                self.IO['io'].update({board['id']: {'value': 0,
                               'update': 0}})
            elif int(board['board_type_id']) == 5:
                pass

    def updateIO(self):
        """
        funzione che aggiorna self.IO['board_io']
        """
        for board_id, data in self.IO['io'].iteritems():
            address = 0
            while data['update'] > 0:
                if data['update'] & 1 == 1:
                    board_io_id = self.M['board_io_m'].get((board_id, address), 0)
                    if board_io_id > 0:
                        bit_value = self.getBitValue(data['value'], address)
                        self.IO['board_io'][board_io_id]['SA'] = bit_value
                data['update'] = int(data['update']) / 2
                address += 1

    def counter(self):
        """
        Funzione che decrementa i timer interni al programma
        """
        for p in self.P:
            if self.P[p]['TA'] > 0:
                self.P[p]['TA'] -= 1

    def getBitValue(self, byteval, idx):
        """
        Return if bit in the byte is 0 or 1
        Ritorna il valore del BIT di un Byte
        """
        if byteval & 1 << idx != 0:
            return 1
        return 0

    def setBit(self, byte, index, x):
        """
        Set bit of byte to x
        Setta a 0 o a 1 il bit di un byte
        Example:  (0b0000, 2, 1) = 0b0100
        Example:  (0b0111, 2, 0) = 0b0011
        """
        mask = 1 << index
        if x:
            byte |= mask
        else:
            byte ^= mask
        return byte
