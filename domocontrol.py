#!/usr/bin/python
import date
import time
import smbus
from db import Database
import datetime
import sht21
import os
import threading

class Domocontrol:
    """Class DomoControl"""

    def __init__(self):
        self.db = Database()
        self.i2c = 0
        self.getBusValue()
        self.A = {}
        self.P = {}
        self.IOThread = []
        self.board_n = ()
        self.board_id = ()
        self.board_type_id = ()
        self.board_address = ()
        self.board_type = ()
        self.board_bin_val = []
        self.board_bin_onchange = []
        self.board_changerequest = []
        self.board_IO_definition = ()
        self.board_io_id = ()
        self.board_io_address = ()
        self.board_io_board_id = ()
        self.PThread = []
        self.prog_n = ()
        self.prog_id = ()
        self.prog_type_id = ()
        self.prog_in_id = ()
        self.prog_out_id = ()
        self.prog_inverted = ()
        self.prog_timer = ()
        self.prog_chrono = ()
        self.prog_enable = ()
        self.prog_counter = []
        self.prog_timeout = []  # dict per variabili temporane usata ad esempio per timeout
        self.dir_root = os.path.dirname(os.path.abspath(__file__))
        self.initialize()

    def getBusValue(self):
        """
        Controlla il numero del divice I2C, puo' essere 0 o 1....
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
        """
        Scrive il valore in byte su I2C
        """
        # print board_address, val
        bus = smbus.SMBus(self.i2c)
        bus.write_byte(board_address, val)

    def runIO(self, board_id, board_type_id, board_n):
        """
        Si occupa di leggere e scrivere i valori degli IO
        """
        if board_type_id == 0:  # None
            pass

        elif board_type_id == 1:  # I2C
            board_id_i2c_val = self.read_i2c(self.board_address[board_n])

            # print "==>>", board_n, board_id_i2c_val, self.board_bin_onchange, self.board_bin_val, self.board_changerequest

            if self.board_bin_val[board_n] != board_id_i2c_val:
                # print "==>>", board_n, board_id_i2c_val, self.board_bin_onchange, self.board_bin_val
                self.board_bin_onchange[board_n] = board_id_i2c_val
                self.board_changerequest[board_n] = 1
                pass

            if self.board_changerequest[board_n] == 1:
                self.board_bin_val[board_n] = self.board_bin_onchange[board_n]
                self.write_i2c(self.board_address[board_n], (self.board_bin_val[board_n] | self.board_IO_definition[board_n]))
                self.board_changerequest[board_n] = 0
            # print "==>>", board_n, board_id_i2c_val, self.board_bin_onchange, self.board_bin_val, self.board_changerequest
            # print

        elif board_type_id == 2:  # RS485
            pass
        elif board_type_id == 3:  # Web
            if self.board_changerequest[board_n] == 1:
                self.board_bin_val[board_n] = self.board_bin_onchange[board_n]
                self.board_changerequest[board_n] = 0

        elif board_type_id == 4 or board_type_id == 6:  # Temperature + humidity
            temperature = round(sht21.SHT21(self.i2c).read_temperature(), 1)
            humidity = round(sht21.SHT21(self.i2c).read_humidity(), 0)
            self.board_bin_val[self.board_type_id.index(4)] = temperature
            self.board_bin_val[self.board_type_id.index(6)] = humidity
            time.sleep(1)
        elif board_type_id == 5:  # PD9535
            pass
        self.IOThread[self.board_id.index(board_id)] = 0
        # print self.board_bin_val, self.board_changerequest, self.board_bin_onchange, board_id, board_type_id

    def InThread(self, board_id, board_type, board_n):
        """
        Thread che richiama getIO()
        """
        threading.Thread(target=self.runIO, args=(board_id, board_type, board_n)).start()

    def getIO(self):
        """
        LOOP si occupa di inizializzare il Thread per l'aggiornamento della lettura/scrittura IO
        """
        for bid in self.board_id:
            if self.IOThread[self.board_id.index(bid)] == 1:
                pass
            else:
                self.IOThread[self.board_id.index(bid)] = 1
                self.InThread(bid, self.board_type_id[self.board_id.index(bid)], self.board_id.index(bid))

    def getIOStatus(self, io_id):
        address = self.board_io_address[self.board_io_id.index(io_id)]
        board_id = self.board_io_board_id[self.board_io_id.index(io_id)]
        # print io_id, address, board_id, self.board_bin_val,
        return self.getBitValue(self.board_bin_val[self.board_id.index(board_id)], address)

    def getBoard_id(self, io_id):
        return self.board_io_board_id[self.board_io_id.index(io_id)]

    def getBoard_address(self, io_id):
        return self.board_io_address[self.board_io_id.index(io_id)]

    def runProg(self, prog_id, prog_n, P):
        """
        Si occupa di leggere e scrivere i valori degli IO
        """
        # print P
        prog_type_id = P['type_id']
        in_status = self.getIOStatus(P['in_id'])
        out_status = self.getIOStatus(P['out_id'])

        if prog_type_id == 1:  # Timer
            # print in_status, self.prog_timer, self.prog_counter
            if in_status == 1:
                self.prog_counter[prog_n] = round(time.time(), 1)
                self.board_bin_onchange[self.board_id.index(self.getBoard_id(P['out_id']))] = self.setBit(self.board_bin_val[self.board_id.index(self.getBoard_id(P['out_id']))], self.getBoard_address(P['out_id']), in_status ^ P['inverted'])
                self.board_changerequest[self.board_id.index(self.getBoard_id(P['out_id']))] = 1
            timer = self.prog_timer[prog_n]
            if time.time() - self.prog_counter[prog_n] > timer:
                self.board_bin_onchange[self.board_id.index(self.getBoard_id(P['out_id']))] = self.setBit(self.board_bin_val[self.board_id.index(self.getBoard_id(P['out_id']))], self.getBoard_address(P['out_id']), in_status ^ P['inverted'])
                self.board_changerequest[self.board_id.index(self.getBoard_id(P['out_id']))] = 1

        elif prog_type_id == 2:  # Timeout
            timer = self.prog_timer[prog_n]
            if in_status == 1 and self.prog_timeout[prog_n] == 0:
                self.prog_timeout[prog_n] = 1
                self.prog_counter[prog_n] = round(time.time(), 1)
            elif in_status == 0 and self.prog_timeout[prog_n] == 1:
                self.prog_timeout[prog_n] = 0

            if timer > time.time() - self.prog_counter[prog_n]:
                self.board_bin_onchange[self.board_id.index(self.getBoard_id(P['out_id']))] = self.setBit(self.board_bin_val[self.board_id.index(self.getBoard_id(P['out_id']))], self.getBoard_address(P['out_id']), 1 ^ P['inverted'])
                self.board_changerequest[self.board_id.index(self.getBoard_id(P['out_id']))] = 1
            else:
                self.board_bin_onchange[self.board_id.index(self.getBoard_id(P['out_id']))] = self.setBit(self.board_bin_val[self.board_id.index(self.getBoard_id(P['out_id']))], self.getBoard_address(P['out_id']), 0 ^ P['inverted'])
                self.board_changerequest[self.board_id.index(self.getBoard_id(P['out_id']))] = 1
            # print in_status, self.prog_timeout[prog_n], timer, time.time() - self.prog_counter[prog_n]

        elif prog_type_id == 3:  # Automatic
            # print self.prog_chrono[prog_n]
            pass


        elif prog_type_id == 4:  # Manual
            if in_status != (out_status ^ P['inverted']):
                self.board_bin_onchange[self.board_id.index(self.getBoard_id(P['out_id']))] = self.setBit(self.board_bin_val[self.board_id.index(self.getBoard_id(P['out_id']))], self.getBoard_address(P['out_id']), in_status ^ P['inverted'])
                # print "board_id:", self.getBoard_id(P['out_id'])
                self.board_changerequest[self.board_id.index(self.getBoard_id(P['out_id']))] = 1
                # print self.board_bin_onchange, self.board_bin_val, self.board_changerequest
        elif prog_type_id == 5:  # Thermostat
            pass
#
        # print 'cambia', self.board_bin_val, self.board_bin_onchange, self.getBoard_address(out_id), in_id_status, self.getBoard_id(out_id)
        self.PThread[prog_n] = 0

    def ProgThread(self, prog_id, prog_n, P):
        """
        Thread che richiama runPro()
        """
        threading.Thread(target=self.runProg, args=(prog_id, prog_n, P)).start()


    def setProg(self):
        """
        LOOP si occupa del programma
        """
        # print self.PThread
        # print self.P
        for pid in self.P:
            prog_n = self.prog_id.index(pid)
            # print self.PThread, self.prog_enable, self.prog_n, self.prog_id, pid, prog_n
            if self.prog_enable[prog_n]:
                if self.PThread[prog_n]:
                    pass
                else:
                    self.PThread[prog_n] = 1
                    self.ProgThread(pid, prog_n, self.P[pid])



    def setClickData(self, data):
        """
        Called from web.py when clicked into I/O
        board_n, address, In value
        """
        io_id = data[0][0]
        address = data[0][1]
        board_id = self.A['board_io'][io_id]['board_id']
        io_value = self.getBitValue(self.board_bin_val[self.board_id.index(board_id)], address)
        next_value = 0 if io_value == 1 else 1
        next_bin = self.setBit(self.board_bin_onchange[self.board_id.index(board_id)], address, next_value)
        self.board_bin_onchange[self.board_id.index(board_id)] = next_bin
        self.board_changerequest[self.board_id.index(board_id)] = 1
        print "io_id:%s,  address:%s,  board_id:%s,  current_value:%s,  next_value:%s  next_bin:%s" %(io_id, address, board_id, io_value, next_value, next_bin)

    def now(self):
        """
        Ritorna l'ora corrente
        """
        return date.now()

    def default(self):
        """
        Set default value at start program
        that is store into database
        """
        q = 'SELECT * FROM board_io ORDER BY board_id, address'
        res = self.db.query(q)
        for r in res:
            if r['board_id'] == 0 or r['board_id'] == 1 or r['board_id'] == 2 or r['board_id'] == 3 or r['board_id'] == 5:  # Tutte le schede che possono essere a valore "0"
                self.board_bin_onchange[self.board_id.index(r['board_id'])] = self.setBit(self.board_bin_onchange[self.board_id.index(r['board_id'])], r['address'], r['default'])
                self.board_changerequest[self.board_id.index(r['board_id'])] = 1  # setta la schede che deve essere aggiornata a 1
        print self.board_bin_onchange, self.board_changerequest


    def initialize(self):
        """
        Funzione di setup
        Imposta il valore di tutti i dizionari per il corretto funzionamento
        """
        print 'Start Domocontrol Setup'

        q = 'SELECT * FROM board ORDER BY id'
        res = self.db.query(q)
        self.A['board'] = {}
        board_id = []
        board_type_id = []
        board_n = []
        board_address = []
        self.board_bin_val = []
        self.board_bin_onchange = []
        self.board_changerequest = []
        n = 0
        for r in res:
            self.A['board'].update({r['id']: r})
            board_n.append(n)
            board_id.append(r['id'])
            board_type_id.append(r['board_type_id'])
            n += 1
            board_address.append(r['address'])
            self.board_bin_val.append(0)
            self.board_bin_onchange.append(0)
            self.IOThread.append(0)
            self.board_changerequest.append(0)


        self.board_id = tuple(board_id)
        self.board_type_id = tuple(board_type_id)
        self.board_n = tuple(board_n)
        self.board_address = tuple(board_address)
        q = 'SELECT id, address, board_id, io_type_id FROM board_io ORDER BY board_id, address'
        res = self.db.query(q)
        board_io_address = []
        board_io_id = []
        board_io_val = []
        tmp_address = []
        tmp_id = []
        tmp_val = []
        self.board_IO_definition = ()
        tmp_IO_definition = []
        tmp_IO_definitionBin = 0
        for lb in self.board_id:
            for r in res:
                if r['board_id'] == lb:
                    tmp_address.append(r['address'])
                    tmp_id.append(r['id'])
                    tmp_val.append(0)
                    if r['io_type_id'] == 0 or r['io_type_id'] == 1 or r['io_type_id'] == 4 or r['io_type_id'] == 5 or r['io_type_id'] == 6 or r['io_type_id'] == 7 or r['io_type_id'] == 8:
                        # print "Zero", r['io_type_id'], bin(tmp_IO_definitionBin), r['address']
                        tmp_IO_definitionBin = self.setBit(tmp_IO_definitionBin, r['address'], 1)
                    else:
                        # print "Uno", r['io_type_id'], bin(tmp_IO_definitionBin), r['address']
                        tmp_IO_definitionBin = self.setBit(tmp_IO_definitionBin, r['address'], 0)

            tmp_IO_definition.append(tmp_IO_definitionBin)
            tmp_IO_definitionBin = 0

            board_io_address.append(tuple(tmp_address))
            board_io_id.append(tuple(tmp_id))
            tmp_address = []
            tmp_id = []
            tmp_val = []
        # print tmp_IO_definition
        self.board_IO_definition = tuple(tmp_IO_definition)


        q = 'SELECT * FROM board_type ORDER BY id'
        res = self.db.query(q)
        board_type = []
        for r in res:
            board_type.append(r['id'])

        self.board_type = tuple(board_type)
        """
        print 'self.board_n      :', self.board_n
        print 'self.board_id     :', self.board_id
        print 'self.board_type_id:', self.board_type_id
        print 'self.board_type   :', self.board_type
        print 'self.board_io_val :', self.board_io_val
        """

        q = 'SELECT * FROM board_io ORDER BY id'
        res = self.db.query(q)
        board_io_id = []
        board_io_address = []
        board_io_board_id = []
        for r in res:
            board_io_id.append(r['id'])
            board_io_address.append(r['address'])
            board_io_board_id.append(r['board_id'])
        self.board_io_id = tuple(board_io_id)
        self.board_io_address = tuple(board_io_address)
        self.board_io_board_id = tuple(board_io_board_id)


        icon_path = os.path.join(self.dir_root, 'static/icon')
        files = [ fn for fn in os.listdir(icon_path) ]
        self.A['icon'] = files
        q = """SELECT * FROM program ORDER BY id"""
        res = self.db.query(q)
        self.PThread = []
        self.P = {}
        prog_n = []
        prog_id = []
        prog_type_id = []
        prog_in_id = []
        prog_out_id = []
        prog_inverted = []
        prog_timer = []
        prog_chrono = []
        prog_enable = []
        prog_counter = []
        self.prog_timeout = []
        n = 0
        for r in res:
            self.P.update({r['id']: r})
            self.PThread.append(0)
            prog_n.append(n)
            prog_id.append(r['id'])
            prog_type_id.append(r['type_id'])
            prog_in_id.append(r['in_id'])
            prog_out_id.append(r['out_id'])
            prog_inverted.append(r['inverted'])

            # Trasforma r['timer'] in secondi
            t = r['timer'].split('-')
            t_sec = int(t[3])
            t_min = int(t[2])
            t_hour = int(t[1])
            t_day = int(t[0])
            timer_sec = t_sec + t_min * 60 + t_hour * 60 * 60 + t_day * 24 * 60 * 60
            prog_timer.append(timer_sec)

            prog_chrono.append(r['chrono'])
            prog_enable.append(r['enable'])
            prog_counter.append(round(time.time(), 1))
            self.prog_timeout.append(0)
            n += 1

        self.prog_n = tuple(prog_n)
        self.prog_id = tuple(prog_id)
        self.prog_type_id = tuple(prog_type_id)
        self.prog_in_id = tuple(prog_in_id)
        self.prog_out_id = tuple(prog_out_id)
        self.prog_inverted = tuple(prog_inverted)
        self.prog_timer = tuple(prog_timer)
        self.prog_chrono = tuple(prog_chrono)
        self.prog_enable = tuple(prog_enable)
        self.prog_counter = prog_counter

        print self.prog_n, self.prog_id, self.prog_type_id, \
            self.prog_in_id, self.prog_out_id, self.prog_inverted, \
            self.prog_timer, self.prog_chrono, self.prog_enable, self.prog_counter

        self.setup_board_io()  # Setup Board_IO
        self.setup_area()  # Setup Area
        self.setup_io_type()  # Setup Io_Type
        self.setup_board_type()  # Setup Board_Type
        self.setup_program_type()  # Setup Program_Type
        self.setup_area_board_io()  # Area_Board_IO

        self.default()  # Chiama la funzione per settare gli stati degli IO come da default

        print 'End Domocontrol Setup'

    def setup_board_io(self):
        q = 'SELECT * FROM board_io ORDER BY id'
        res = self.db.query(q)
        self.A['board_io'] = {}
        for r in res:
            self.A['board_io'].update({r['id']: r})

    def setup_area(self):
        q = 'SELECT id, name, description, sort FROM area ORDER BY sort'
        res = self.db.query(q)
        self.A['area'] = {}
        for r in res:
            self.A['area'].update({r['id']: r})

    def setup_io_type(self):
        q = 'SELECT id, type, name, description FROM io_type'
        res = self.db.query(q)
        self.A['io_type'] = {}
        for r in res:
            self.A['io_type'].update({r['id']: r})

    def setup_board_type(self):
        q = 'SELECT * FROM board_type'
        res = self.db.query(q)
        self.A['board_type'] = {}
        for r in res:
            self.A['board_type'].update({r['id']: r})

    def setup_program_type(self):
        q = 'SELECT * FROM program_type'
        res = self.db.query(q)
        self.A['program_type'] = {}
        for r in res:
            self.A['program_type'].update({r['id']: r})

    def setup_area_board_io(self):
        """
        Query che mette in relazione gli IO ordinati per AREA.
        Il risutato viene usato sul WEB menu_status
        """
        q = """SELECT a.id AS area_id, a.name AS area_name, a.description AS area_description, bio.id AS  board_io_id,  bio.io_type_id AS board_io_io_type_id,
                bio.name AS board_io_name, bio.description AS board_io_description, bio.address AS board_io_address, bio.board_id AS board_io_board_id,
                bio.icon_on AS board_io_icon_on, bio.icon_off AS board_io_icon_off
            FROM board_io AS bio
            LEFT JOIN area AS a ON bio.area_id=a.id
            ORDER BY a.sort
            """
        res = self.db.query(q)
        self.A['area_board_io'] = {}
        for r in res:
            self.A['area_board_io'].update({r['board_io_id']: r})

    def getData(self, data):
        """
        Ritorna qualsiasi variabile (es. "self.A")
        """
        return eval(data)

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
            # print "unoo", mask, byte
        else:
            byte &= ~mask
            # print "zero", mask, byte
        return byte
