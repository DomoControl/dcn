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
        self.db = Database() # classe database
        self.i2c = 0
        self.getBusValue() # Setta il corretto device
        self.A = {}
        self.P = {}

        self.mBoard = [] # matrive board
        self.mBoard_io = [] # matrice IO
        self.mProg = [] # matrice programma

        self.area_id = ()

        self.dir_root = os.path.dirname(os.path.abspath(__file__))
        self.initialize()

    def getBusValue(self):
        """
        Controlla il numero del divice I2C, puo' essere 0 o 1....
        """
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

        # self.log('Self.Mboard', self.mBoard)
        if board_type_id == 0:  # None
            pass

        elif board_type_id == 1:  # I2C
            # self.log('mBoard', self.mBoard)
            if self.mBoard[8][board_n] == 1: # se board_update e' settato:
                self.mBoard[6][board_n] = self.mBoard[7][board_n] # Aggiorna board_bin_val con board_bin_val_new
                self.write_i2c(self.mBoard[3][board_n], (self.mBoard[6][board_n] | self.mBoard[9][board_n])) # Aggiorna I2C out
                self.mBoard[8][board_n] = 0

            board_id_i2c_val = self.read_i2c(self.mBoard[3][board_n]) # Get byte valore I2C board
            if self.mBoard[6][board_n] != board_id_i2c_val: # check if board_bin_val e' cambiato
                self.mBoard[7][board_n] = self.mBoard[6][board_n] = board_id_i2c_val # aggiorna board_bin_val
                self.write_i2c(self.mBoard[3][board_n], (self.mBoard[6][board_n] | self.mBoard[9][board_n])) # Aggiorna I2C out


        elif board_type_id == 2:  # RS485
            pass

        elif board_type_id == 3:  # Webs
            if self.mBoard[8][board_n] == 1:
                self.mBoard[6][board_n] = self.mBoard[7][board_n]
                self.mBoard[8][board_n] = 0

        elif board_type_id == 4 or board_type_id == 6:  # Temperature + humidity
            a = sht21.SHT21(self.i2c)
            if board_type_id == 4:
                time.sleep(0.33)
                self.mBoard[6][board_n] = round(a.read_temperature(), 1)
            if board_type_id == 6:
                time.sleep(0.5)
                self.mBoard[6][board_n] = round(a.read_humidity(), 0)
            # time.sleep(1)

        elif board_type_id == 5:  # PD9535
            pass

        # print self.mBoard[6]
        self.mBoard[5][board_n] = 0
        # self.log('board', self.mBoard)

    def InThread(self, board_id, board_type, board_n):
        """
        Thread che richiama getIO()
        """
        # print board_id, board_type, board_n
        threading.Thread(target=self.runIO, args=(board_id, board_type, board_n)).start()

    def getIO(self):
        """
        LOOP si occupa di inizializzare il Thread per l'aggiornamento della lettura/scrittura IO
        """
        for bn in self.mBoard[0]: # Fa la scansione delle board
            if self.mBoard[2][bn] == 1: # check se la board e' abilitata
                if self.mBoard[5][bn] == 0: # Se il thread non e' attivo, lo attiva
                    self.mBoard[5][bn] = 1
                    self.InThread(self.mBoard[1][bn], self.mBoard[4][bn], bn) # chiama a funzione per update IO


    def getIOStatus(self, io_id):
        """
        Ritorna il valore del bit del byte
        """
        # self.log('mBoard_io', self.mBoard_io)
        address = self.mBoard[3][self.getBoard_n(io_id)]
        return self.getBitValue(self.mBoard[6][self.getBoard_n(io_id)], address)

    def getBoard_id(self, io_id):
        """
        Ritorna board_id da io_id
        """
        return self.mBoard_io[4][self.mBoard_io[1].index(io_id)]


    def getBoard_address(self, io_id):
        """
        Ritorna board_address
        """
        return self.mBoard_io[5][self.mBoard_io[1].index(io_id)]

    def getBoard_n(self, io_id):
        """
        Ritorna board_b
        """
        return self.mBoard[1].index(self.getBoard_id(io_id))

    def runProg(self, prog_n, prog_type_id):
        """
        Si occupa di leggere e scrivere i valori degli IO
        """
        # print 'prog'
        # self.log('mProg', self.mProg)
        # self.log('mBoard', self.mBoard)self.log

        # self.log('mBoard', self.mBoard)
        in_id = self.mProg[2][prog_n]
        in_status = self.getIOStatus(in_id)
        out_id = self.mProg[5][prog_n]
        out_status = self.getIOStatus(out_id)
        inverted = self.mProg[4][prog_n]

        if prog_type_id == 1:  # Timer OK
            if in_status == 1: # Deve accendersi
                self.mProg[10][prog_n] = round(time.time(), 1) # Mette su Counter l'ora corrente
                self.mBoard[7][self.getBoard_n(out_id)] = self.setBit(self.mBoard[6][self.getBoard_n(out_id)], self.getBoard_address(out_id), in_status ^ inverted)
                self.mBoard[8][self.getBoard_n(out_id)] = 1
            timer = self.mProg[7][prog_n]
            # print time.time(), self.mProg[10][prog_n], timer, time.time() - self.mProg[10][prog_n]
            if time.time() - self.mProg[10][prog_n] > timer:
                self.mBoard[7][self.getBoard_n(out_id)] = self.setBit(self.mBoard[6][self.getBoard_n(out_id)], self.getBoard_address(out_id), inverted)
                self.mBoard[8][self.getBoard_n(out_id)] = 1

        elif prog_type_id == 2:  # Timeout
            """
            Out = 1 solo se in_status == 1 e counter non e' scaduto
            """
            timer = self.mProg[7][prog_n] # Tempo massimo accensione
            counter = time.time() - self.mProg[10][prog_n]
            # print 'in_status:', in_status, 'timer:', timer, 'counter:', time.time(), self.mProg[10][prog_n], counter, counter <= timer
            if in_status == 1 and counter >= timer : #
                # print "A"
                out = inverted
            elif in_status == 0 and counter >= timer:
                # print "B"
                self.mProg[10][prog_n] = time.time()
                out = inverted
            elif in_status == 1 and counter <= timer:
                # print "C"
                out = not inverted
            elif in_status == 0 and counter <= timer:
                # print "D"
                self.mProg[10][prog_n] = time.time()
                out = inverted

            if out != self.mBoard[7][self.mBoard[1].index(self.getBoard_id(out_id))]:
                self.mBoard[7][self.getBoard_n(out_id)] = self.setBit(self.mBoard[6][self.getBoard_n(out_id)], self.getBoard_address(out_id), out)
                self.mBoard[8][self.getBoard_n(out_id)] = 1

        elif prog_type_id == 3:  # Automatic
            pass

        elif prog_type_id == 4:  # Manual OK
                val = self.setBit(self.mBoard[6][self.mBoard[1].index(self.getBoard_id(out_id))], self.getBoard_address(out_id), in_status ^ self.mProg[4][prog_n])
                if val != self.mBoard[7][self.mBoard[1].index(self.getBoard_id(out_id))]:
                    self.mBoard[7][self.mBoard[1].index(self.getBoard_id(out_id))] = val
                    self.mBoard[8][self.mBoard[1].index(self.getBoard_id(out_id))] = 1

        elif prog_type_id == 5:  # Thermostat
            pass

        self.mProg[11][prog_n] = 0

    def ProgThread(self, prog_n, prog_type_id):
        """
        Thread che richiama runPro()
        """
        threading.Thread(target=self.runProg, args=(prog_n, prog_type_id)).start()


    def setProg(self):
        """
        LOOP si occupa del programma
        """
        for prog_n in self.mProg[0]: # loog programma
            if self.mProg[9][prog_n]: # Check se programma abilitato
                if self.mProg[11][prog_n] == 0: # Se Thread == 0 esegui
                    self.mProg[11][prog_n] = 1
                    self.ProgThread(prog_n, self.mProg[6][prog_n])

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



    def setClickData(self, data):
        """
        Called from web.py when clicked into I/O
        board_n, address, In value
        """
        io_id = data[0][0]
        address = data[0][1]
        board_id = self.mBoard_io[4][self.mBoard_io[1].index(io_id)]
        io_value = self.getBitValue(self.mBoard[6][self.mBoard[1].index(board_id)], address)

        next_value = 0 if io_value == 1 else 1

        next_bin = self.setBit(self.mBoard[7][self.mBoard[1].index(board_id)], address, next_value)
        # print "next_bin:", next_bin, 'elf.mBoard[7]', self.mBoard[7][self.mBoard[1].index(board_id)], 'Address:', address, 'Value:', io_value

        self.mBoard[7][self.mBoard[1].index(board_id)] = next_bin
        self.mBoard[8][self.mBoard[1].index(board_id)] = 1
        # self.log('mBoard', self.mBoard)
        print "io_id:%s,  address:%s,  board_id:%s,  current_value:%s,  next_value:%s  next_bin:%s" %(io_id, address, board_id, io_value, next_value, next_bin)

    def now(self):
        """
        Ritorna l'ora corrente
        """
        return date.now()

    def setDefault(self):
        """
        Set default value at start program
        that is store into database
        """
        q = 'SELECT * FROM board_io ORDER BY board_id, address'
        res = self.db.query(q)
        for r in res:
            if r['board_id'] == 0 or r['board_id'] == 1 or r['board_id'] == 2 or r['board_id'] == 3 or r['board_id'] == 5:  # Tutte le schede che possono essere a valore "0"
                self.mBoard[7][self.mBoard[1].index(r['board_id'])] = self.setBit(self.mBoard[7][self.mBoard[1].index(r['board_id'])], r['address'], r['default'])
                self.mBoard[8][self.mBoard[1].index(r['board_id'])] = 1  # setta la schede che deve essere aggiornata a 1
        # self.log('self.mBoard', self.mBoard)




    def log(self, name, data):
        """
        Funzione che formatta la stampa a video degli oggetti
        """
        print name
        if type(data) == tuple:
            print "**************"
        elif type(data) == list:
            for d in data:
                print d
        print

    def initialize(self):
        """
        Funzione di setup
        Imposta il valore di tutti i dizionari per il corretto funzionamento
        """
        print 'Start Domocontrol Setup'

        q = 'SELECT * FROM board ORDER BY id'
        res = self.db.query(q)
        self.A['board'] = {}
        board_n = []
        board_id = []
        board_enable = []
        board_type_id = []
        IOThread = []
        board_bin_val = []
        board_bin_val_new = []
        board_update = []
        board_address = []

        n = 0
        for r in res:
            self.A['board'].update({r['id']: r})
            board_n.append(n)
            n += 1
            board_id.append(r['id'])
            board_enable.append(r['enable'])
            board_address.append(r['address'])
            board_type_id.append(r['board_type_id'])
            IOThread.append(0)
            board_bin_val.append(0)
            board_bin_val_new.append(0)
            board_update.append(0)

        # Matrice Board
        self.mBoard.append(tuple(board_n))
        self.mBoard.append(tuple(board_id))
        self.mBoard.append(tuple(board_enable))
        self.mBoard.append(tuple(board_address))
        self.mBoard.append(tuple(board_type_id))
        self.mBoard.append(IOThread)
        self.mBoard.append(board_bin_val)
        self.mBoard.append(board_bin_val_new)
        self.mBoard.append(board_update)
        # self.log('Matrice Board', self.mBoard)


        q = 'SELECT id, address, board_id, io_type_id FROM board_io ORDER BY board_id, address'
        res = self.db.query(q)
        board_io_address = []
        board_io_id = []
        board_io_val = []
        tmp_address = []
        tmp_id = []
        tmp_val = []
        tmp_IO_definition = []
        tmp_IO_definitionBin = 0
        for lb in self.mBoard[1]:
            for r in res:
                if r['board_id'] == lb:
                    tmp_address.append(r['address'])
                    tmp_id.append(r['id'])
                    tmp_val.append(0)
                    if r['io_type_id'] == 0 or r['io_type_id'] == 1 or r['io_type_id'] == 4 or r['io_type_id'] == 5 or r['io_type_id'] == 6 or r['io_type_id'] == 7 or r['io_type_id'] == 8:
                        tmp_IO_definitionBin = self.setBit(tmp_IO_definitionBin, r['address'], 1)
                    else:
                        tmp_IO_definitionBin = self.setBit(tmp_IO_definitionBin, r['address'], 0)

            tmp_IO_definition.append(tmp_IO_definitionBin)
            tmp_IO_definitionBin = 0

            board_io_address.append(tuple(tmp_address))
            board_io_id.append(tuple(tmp_id))
            tmp_address = []
            tmp_id = []
            tmp_val = []


        q = 'SELECT * FROM board_type ORDER BY id'
        res = self.db.query(q)
        board_type = []
        for r in res:
            board_type.append(r['id'])


        q = 'SELECT * FROM board_io ORDER BY id'
        res = self.db.query(q)
        board_io_n = []
        board_io_id = []
        board_io_address = []
        board_io_board_id = []
        board_io_type_id = []
        board_io_enable = []
        board_io_area_id = []
        board_io_definition = []
        n = 0
        for r in res:
            board_io_n.append(n)
            board_io_id.append(r['id'])
            board_io_type_id.append(r['io_type_id'])
            board_io_enable.append(r['enable'])
            board_io_board_id.append(r['board_id'])
            board_io_address.append(r['address'])
            board_io_area_id.append(r['area_id'])
            if r['io_type_id'] == 2 or r['io_type_id'] == 3: # IO = uscite
                board_io_definition.append(0)
            else: # IO = ingressi
                board_io_definition.append(1)
            n += 1

        icon_path = os.path.join(self.dir_root, 'static/icon')
        files = [ fn for fn in os.listdir(icon_path) ]
        self.A['icon'] = files

        # Matrice Board_IO
        self.mBoard_io.append(tuple(board_io_n))
        self.mBoard_io.append(tuple(board_io_id))
        self.mBoard_io.append(tuple(board_io_type_id))
        self.mBoard_io.append(tuple(board_io_enable))
        self.mBoard_io.append(tuple(board_io_board_id))
        self.mBoard_io.append(tuple(board_io_address))
        self.mBoard_io.append(tuple(board_io_area_id))
        self.mBoard_io.append(tuple(board_io_definition))

        # Set mBoard[9] -> definizione ingressi / uscite: 0=output, 1=input
        board_definition = {}
        board_definition1 = []
        for x in self.mBoard_io[0]:
            # print x, self.mBoard_io[4][x], self.mBoard_io[7][x], self.mBoard_io[5][x]
            if not self.mBoard_io[4][x] in board_definition: # Add board_id into list
                board_definition.update({self.mBoard_io[4][x]: 0})
            if self.mBoard_io[7][x] == 1 and self.mBoard_io[7][x] == 1 : # IO = input
                board_definition[self.mBoard_io[4][x]] += 2 ** self.mBoard_io[5][x]
        for x in self.mBoard[1]:
            # print x, board_definition.get(x, 1)
            board_definition1.append(board_definition.get(x, 1))
        self.mBoard.append(board_definition1)
        self.log('mBoard', self.mBoard)



        q = """SELECT * FROM program ORDER BY id"""
        res = self.db.query(q)
        self.P = {}
        prog_n = []
        prog_id = []
        prog_in_id = []
        prog_delay = []
        prog_inverted = []
        prog_out_id = []
        prog_type_id = []
        prog_timer = []
        prog_chrono = []
        prog_enable = []
        prog_counter = []
        prog_PTHread = []

        n = 0
        for r in res:
            self.P.update({r['id']: r})
            prog_n.append(n)
            prog_id.append(r['id'])
            prog_type_id.append(r['type_id'])
            prog_in_id.append(r['in_id'])
            prog_delay.append(r['delay'])
            prog_inverted.append(r['inverted'])
            prog_out_id.append(r['out_id'])

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
            prog_PTHread.append(0)
            prog_counter.append(round(time.time(), 1))
            n += 1


        # Matrice Program
        self.mProg.append(tuple(prog_n))
        self.mProg.append(tuple(prog_id))
        self.mProg.append(tuple(prog_in_id))
        self.mProg.append(tuple(prog_delay))
        self.mProg.append(tuple(prog_inverted))
        self.mProg.append(tuple(prog_out_id))
        self.mProg.append(tuple(prog_type_id))
        self.mProg.append(tuple(prog_timer))
        self.mProg.append(tuple(prog_chrono))
        self.mProg.append(tuple(prog_enable))
        self.mProg.append(prog_counter)
        self.mProg.append(prog_PTHread)
        # self.log('Matrice Prog', self.mProg)


        self.setup_board_io()  # Setup Board_IO
        self.setup_area()  # Setup Area
        self.setup_io_type()  # Setup Io_Type
        self.setup_board_type()  # Setup Board_Type
        self.setup_program_type()  # Setup Program_Type
        self.setup_area_board_io()  # Area_Board_IO

        self.setDefault()  # Chiama la funzione per settare gli stati degli IO come da default

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
        area_id = []
        for r in res:
            self.A['area'].update({r['id']: r})
            area_id.append(r['id'])
        self.area_id = tuple(area_id)

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
