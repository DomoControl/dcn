#!/usr/bin/python
from flask import Flask, request, render_template, g, session, jsonify, redirect, url_for, Response, json
from flask.ext.bootstrap import Bootstrap
# from flask_sse import sse, send_event
from db import Database
import sys
from date import now  # get time function
import threading
from threading import Thread
import domocontrol
from flask.ext.babel import Babel
from config import LANGUAGES
import time
import copy
import traceback
from gevent import monkey
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, close_room, disconnect
# import gevent
# from gevent.pywsgi import WSGIServer
monkey.patch_all()
print("Begin")

app = Flask(__name__)
# app.debug = True
app.debug = False

app.config['SECRET_KEY'] = 'secret!123654887'
app.config.from_pyfile('config.py')
app.config.from_object('config')
socketio = SocketIO(app)
thread = None

babel = Babel(app)
bootstrap = Bootstrap(app)

DATABASE = './db/db.sqlite'
db = Database(dbname=DATABASE)  # metodi per database
d = domocontrol.Domocontrol()

P = {}  # Dict with Program
PCopy = {}  # Copy P dictionary
A = {}  # All other db information
ACopy = {}  # Copy A dictionary
IO = {}  # Content IO status (menu status)
IOCopy = {}  # Copy IO dictionary


@app.route('/lang/it')
def lang(language=None):
    setattr(g, 'lang', language)


@babel.localeselector
def get_locale():
    # if a user is logged in, use the locale from the user settings
    user = getattr(g, 'user', None)
    if user is not None:
        return user.locale
    # otherwise try to guess the language from the user accept
    # header the browser transmits.  We support de/fr/en in this
    return request.accept_languages.best_match(['it', 'en'])


def setLog():  # Da finire. Serve per tracciare l'IP
    # if session['privilege']
    userAgentString = request.headers.get('User-Agent')
    if not request.remote_addr[0:9] == '192.168.1':
        res = db.query("INSERT INTO log (command,ip) VALUES('{}', '{}')".format(request.url, request.remote_addr))


def checkPermission(permission=255, error=''):  # Check if user is logged and the privileve
    """
    Privilege session:
    xxxx
    8421
    1: Log - 2: View - 4: Setup  -  128: Admin
    """
    if 'logged_in' in session and session['logged_in'] == True and (now() - session['timestamp']).total_seconds() < session['sessionTimeout']:  # Test if logged
        session['timestamp'] = now()
    else:
        return 'login'

    priv = int(session['privilege'])
    if priv >= permission:  # check permission for LOG
        return 0
    else:
        return 'no_permission'

@app.route('/getTime')  # return datetime now() to show in footer
def getTime():
    return jsonify(result=now().strftime("%a  %d/%m/%y   %H:%M:%S"))

event_menu_status_start = 0
def event_menu_status(start = 0):
    """
    Send data to menu_status by server sent event (SSE)
    For something more intelligent, take a look at Redis pub/sub
    stuff. A great example can be found here https://github.com/jakubroztocil/chat
    """
    board_bin_val = list(d.getData('self.mBoard[6]'))
    A = d.getData('self.A')
    area_board_io = d.getData('self.A["area_board_io"]').copy()
    area = d.getData('self.A["area"]').copy()
    board_id = d.getData('self.mBoard[1]')
    P = d.getData('self.P')
    program_type = d.getData('self.A["program_type"]')
    global event_menu_status_start
    print 'event_menu_status', event_menu_status_start

    while True:
        page_reload = 0
        change = 0

        # print "event_menu_status"

        if board_bin_val != d.getData('self.mBoard[6]'):
            print "cambia board_bin_val", board_bin_val
            board_bin_val = list(d.getData('self.mBoard[6]'))
            change += 1

        if board_id != d.getData('self.mBoard[1]'):
            # print "cambia board_id", board_id
            board_id = list(d.getData('self.mBoard[1]'))
            change += 1

        if area_board_io != d.getData('self.A["area_board_io"]'):
            # print "cambia area_board_io", area_board_io
            area_board_io = d.getData('self.A["area_board_io"]').copy()
            page_reload = 1

        # print "cambia area", area, d.getData('self.A["area"]'), d.getData('self.A["area"]') == area
        if area != d.getData('self.A["area"]'):
            # print "cambia area", area
            area = d.getData('self.A["area"]').copy()
            page_reload = 1

        if P != d.getData('self.P'):
            # print "cambia P", P
            P = d.getData('self.P').copy()
            page_reload = 1

        if program_type != d.getData('self.A["program_type"]'):
            program_type = d.getData('self.A["program_type"]').copy()
            page_reload = 1

        mProg = d.getData('self.mProg')
        counter = []
        for p in mProg[6]:
            counter.append(time.time() - p)
        print counter


        if event_menu_status_start or change or page_reload:
            event_menu_status_start = 0
            # print "PageReload", page_reload, 'change', change, board_bin_val, P
            socketio.emit('menu_status_data', {'board_bin_val': board_bin_val,
                'area_board_io': area_board_io, 'area': area, 'board_id': board_id, 'page_reload': page_reload, 'P': P, 'program_type': program_type},
                namespace='/menu_status')
        else:
            # print "PageReload", page_reload, 'NO changed'
            time.sleep(1)

@socketio.on('menu_status_start', namespace='/menu_status')
def menu_status_start(message):
    global event_menu_status_start
    event_menu_status_start = 1
    print "menu_status_start:", message

@app.route('/menu_status')
def menu_status():
    permission = checkPermission(2)  # check login and privilege
    if permission: return redirect(url_for(permission))

    A = d.getData('self.A')
    area_id = d.getData('self.area_id')

    global thread
    if thread is None:
        thread = Thread(target=event_menu_status)
        thread.start()
    return render_template("menu_status.html", A=A, area_id=area_id)

@socketio.on('change_menu_status', namespace='/menu_status')
def change_menu_status(message):
    """
    Funzione chiamata dal pulsante IO per cambiare stato
    (board_n, address)
    """
    print "Ckick by web, Update IO ", message
    d.setClickData(message)  # Chiama la funzione che aggiorna il dict con il vaore del tasto premuto

@socketio.on('menu_status_getInfo', namespace='/menu_status')
def menu_status_getInfo(*message):
    """
    Funzione chiamata dal pulsante "?", ritorna tutti i dati relativi al quel pulsante
    (board_id, address)
    """
    print "menu_status_getInfo", message  # Chiama la funzione che aggiorna il dict con il vaore del tasto premuto
    A = d.getData('self.A')
    board_io = A['board_io'][message[0]['board_io_id']]
    title = '%s - %s' %(board_io['name'], board_io['description'])
    area = A['area'][board_io['area_id']]
    board = A['board'][board_io['board_id']]
    board_type = A['board_type'][board_io['board_id']]
    io_type = A['io_type'][board_io['io_type_id']]
    P = d.getData('self.P')
    prog_id = prog_name = prog_description = ''

    for p in P:
        if P[p]['in_id'] == message[0]['board_io_id'] or P[p]['out_id'] == message[0]['board_io_id']:
            prog_id = P[p]['id']
            prog_name = P[p]['name']
            prog_description = P[p]['description']

    text = """
            <div class="row"><div class="col-xs-4 col-md-4">Area</div><div class="col-xs-8 col-md-8">%s - %s</div></div>
            <div class="row"><div class="col-xs-4 col-md-4">Board</div><div class="col-xs-8 col-md-8">%s - %s</div></div>
            <div class="row"><div class="col-xs-4 col-md-4">Board Type</div><div class="col-xs-8 col-md-8">%s</div></div>
            <div class="row"><div class="col-xs-4 col-md-4">IO Type</div><div class="col-xs-8 col-md-8">%s</div></div>
            <div class="row" style="background:#D2D7EF;"><div class="col-xs-4 col-md-4">Program</div><div class="col-xs-8 col-md-8">ID: %s<br>Name: %s<br>Decription: %s</div></div>
        """\
    %(area['id'], area['description'], board['id'], board['description'], board_type['description'], io_type['description'], prog_id, prog_name, prog_description)
    socketio.emit('menu_status_getInfo', {'title': title, 'text': text}, namespace='/menu_status' )

@socketio.on('menu_status_getIoCheck', namespace='/menu_status')
def menu_status_getIoCheck(message):
    """
    Chamata da IO web per definire il tipo di IO oppure per l'associazione dei vari IO in programmi
    """
    print 'menu_status_getIoCheck', message

@socketio.on('menu_status_getProgIn', namespace='/menu_status')
def menu_status_getProgIn(prog_id):
    """
    Chamata da IO web. Mostra Program_ID
    """

    print 'menu_status_getProgId', prog_id['prog_id'][1:]
    title = 'Program ID: %s' %(prog_id['prog_id'])
    text = """
            <div class="row" style="background:#D2D7EF;"><div class="col-xs-4 col-md-4">Program</div><div class="col-xs-8 col-md-8">ID: %s</div></div>
        """\
    %(prog_id['prog_id'])

    socketio.emit('menu_status_getInfo', {'title': title, 'text': text}, namespace='/menu_status' )


@app.route('/setup_program_type', methods=["GET", "POST"])
def setup_program_type():
    permission = checkPermission(2)  # check login and privilege
    if permission: return redirect(url_for(permission))

    if request.method == "POST":
        f = request.form
        db.setForm('UPDATE', f.to_dict(), 'program_type')
    q = 'SELECT * FROM program_type'
    res = db.query(q)
    print "Setup_Program ", res
    return render_template("setup_program_type.html", data=res)


@app.route('/setup_area', methods=["GET", "POST"])
def setup_area():
    permission = checkPermission(2)  # check login and privilege
    if permission: return redirect(url_for(permission))

    if request.method == "POST":
        f = request.form  # get input value
        db.setForm('UPDATE', f.to_dict(), 'area')  # recall db.setForm to update query. UPDATE=Update method, f.to_dict=dictionary with input value, area:database table
        d.setup_area()
        d.setup_area_board_io()
    q = 'SELECT * FROM area ORDER by sort'
    res = db.query(q)
    return render_template("setup_area.html", data=res)


@app.route('/menu_sensor', methods=["GET", "POST"])
def menu_sensor(chartID='chart_ID', chart_type='line', chart_height=350):
    permission = checkPermission(2)  # check login and privilege
    if permission: return redirect(url_for(permission))

    q = 'SELECT * FROM sensor WHERE type=1 ORDER BY datetime DESC LIMIT 248'
    temperature = db.query(q)
    temp = []
    categories = []
    for t in temperature:
        micros = float(time.mktime(time.strptime(t['datetime'], '%Y-%m-%d %H:%M:%S')) * 1000)
        temp.append(t['value'])
        categories.append(micros)
    temp.reverse()
    categories.reverse()

    q = 'SELECT * FROM sensor WHERE type=2 ORDER BY datetime DESC LIMIT 248'
    humidity = db.query(q)
    hum = []
    for h in humidity:
        micros = int(time.mktime(time.strptime(h['datetime'], '%Y-%m-%d %H:%M:%S')))
        hum.append(h['value'])
    hum.reverse()

    chart = {"renderTo": chartID, "type": chart_type, "height": chart_height, }

    series = [{"yAxis": 0, "name": 'Temperature', "data": temp}, {"yAxis": 1, "name": 'Humidity', "data": hum}]
    tooltip = {"backgroundColor": '#00FFC5', "borderColor": 'black', "borderRadius": 10, "borderWidth": 3}
    title = {"text": 'Temperature / Humidity'}
    xAxis = {"title": {"text": 'Date'}, "type": 'datetime', "categories": categories, "dateTimeLabelFormats": {"month": '%e. %b', "year": '%b'}, "tickPixelInterval": 20}

    yAxis = [{"title": {"text": 'Temperature'}}, {"title": {"text": 'Humidity'}, "opposite": 'true'}]
    tooltip = {"headerFormat": '<b>{series.name}</b><br>', "pointFormat": '{point.x:%e. %b}: {point.y:.2f} m'}
    print chartID, chart, series, title, xAxis, yAxis, tooltip
    return render_template('menu_sensor.html', chartID=chartID, chart=chart, series=series, title=title, xAxis=xAxis, yAxis=yAxis, tooltip=tooltip)


@app.route('/setup_privilege', methods=["GET", "POST"])
def setup_privilege():
    permission = checkPermission(2)  # check login and privilege
    if permission: return redirect(url_for(permission))

    if request.method == "POST":
        f = request.form
        db.setForm('UPDATE', f.to_dict(), 'privilege')
    q = 'SELECT * FROM privilege'
    res = db.query(q)
    return render_template("setup_privilege.html", data=res)


@app.route('/setup_translation', methods=["GET", "POST"])
def setup_translation():
    permission = checkPermission(2)  # check login and privilege
    if permission: return redirect(url_for(permission))

    if request.method == "POST":
        f = request.form
        q = 'UPDATE translation SET en="{}", it="{}", de="{}" WHERE id="{}" '.format(f["en"], f["it"], f["de"], f["id"])
        db.query(q)
    q = 'SELECT * FROM translation'
    res = db.query(q)
    return render_template("setup_translation.html", data=res)


@app.route('/setup_board_type', methods=["GET", "POST"])
def setup_board_type():
    permission = checkPermission(2)  # check login and privilege
    if permission: return redirect(url_for(permission))

    if request.method == "POST":
        f = request.form
        db.setForm('UPDATE', f.to_dict(), 'board_type')
    q = 'SELECT * FROM board_type'
    res = db.query(q)
    return render_template("setup_board_type.html", data=res)


@app.route('/setup_board', methods=["GET", "POST"])
def setup_board():
    permission = checkPermission(2)  # check login and privilege
    if permission: return redirect(url_for(permission))

    if request.method == "POST":
        f = request.form
        if f['submit'] == 'Save':
            if 'enable' in f:
                enable = 1
            else:
                enable = 0
            q = 'UPDATE board SET id="{}", name="{}", description="{}", enable="{}", address="{}", board_type_id="{}" WHERE id="{}"'\
                .format(f["id"], f["name"], f["description"], enable, f["address"], f["board_type"], f["id"])
            db.query(q)
            q = 'SELECT * FROM board'
            res = db.query(q)
            q = 'SELECT * FROM board_type ORDER BY id'
            board_type = db.query(q)
        elif f['submit'] == 'Edit IO':
            return redirect(url_for('setup_board_io', id=f['id']))
        elif f['submit'] == 'Add':
            if 'enable' in f:
                enable = 1
            else:
                enable = 0
            q = 'INSERT INTO board (name, description, enable, address, board_type_id) VALUES ("{}", "{}", "{}", "{}", "{}")'\
                .format(f['name'], f['description'], enable, f['address'], f['board_type'])
            db.query(q)
            q = 'SELECT * FROM board'
            res = db.query(q)
            q = 'SELECT * FROM board_type ORDER BY id'
            board_type = db.query(q)
        elif f['submit'] == 'Delete':
            q = 'DELETE FROM board WHERE id="{}"'.format(f['id'])
            db.query(q)
    q = 'SELECT * FROM board'
    res = db.query(q)
    q = 'SELECT * FROM board_type ORDER BY id'
    board_type = db.query(q)
    return render_template("setup_board.html", data=res, board_type=board_type)


def checkEnable(io_id, enable):
    """
    Controlla se board_io_id e' usato nel programma.
    Solo un ingresso per programma
    """
    if enable:  # ritorna se enable = 1
        return 0

    in_io = d.getData('self.mProg[2]')
    out_io = d.getData('self.mProg[5]')
    io = in_io + out_io
    print 'Enable:%s, io:%s, io_id:%s ' %(enable, io, io_id)

    if int(io_id) in io:
        return io_id
    else:
        return 0


@app.route('/setup_board_io', methods=["GET", "POST"])
def setup_board_io():
    permission = checkPermission(2)  # check login and privilege
    if permission: return redirect(url_for(permission))

    msg = msg_type = ''
    if request.method == "POST":
        f = request.form
        # print(f)
        if f['submit'] == 'Save':
            if 'enable' in f:
                enable = 1
            else:
                enable = 0
            # print 'f["id"]: ', f["id"], '  ', "enable:", enable

            if checkEnable(f["id"], enable):  # Controlla se l'ingresso e' gia' usato da Program
                msg_type = 'warning'
                msg = "Cannot disable I/O id:%s used in setup_board_io because it is used into Program. First delete program or change IN/OUT into it." % (checkEnable(f["id"], enable))
            else:
                q = 'UPDATE board_io SET id="{}", io_type_id="{}", name="{}", description="{}", area_id="{}", enable="{}", board_id="{}", address="{}", icon_on="{}", icon_off="{}" WHERE id="{}"'\
                    .format(f['id'], f['io_type_id'], f['name'], f['description'], f['area_id'], enable, f['board_id'], f['address'], f['icon_on'], f['icon_off'], f['id'])
                db.query(q)
                d.setup_area_board_io()
                d.setup_board_io()
                print q
        elif f['submit'] == 'Add IO':
            if 'enable' in f:
                enable = 1
            else:
                enable = 0
            q = 'INSERT INTO board_io (io_type_id, name, description, area_id, enable, board_id, address , icon_on, icon_off) VALUES ("{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}")'\
                .format(f['io_type_id'], f["name"], f["description"], f["area_id"], enable, f['board_id'], f["address"], f['icon_on'], f['icon_off'] )
            db.query(q)
            d.setup_area_board_io()
            d.setup_board_io()
        elif f['submit'] == 'Delete':
            if checkEnable(f["id"]):
                msg_type = 'warning'
                msg = 'Cannot delete I/O used in Program, first change Program '
            else:
                q = "DELETE FROM board_io WHERE id={}".format(f['id'])
                db.query(q)
                d.area_board_io()
                d.setup_board_io()

    id = request.args['id']
    q = 'SELECT * FROM board_io WHERE board_id={}'.format(id)
    res = db.query(q)
    q = 'SELECT * FROM board WHERE id={}'.format(id)
    board = db.query(q)
    q = 'SELECT * FROM board_type WHERE id={}  ORDER BY id'.format(board[0]['board_type_id'])
    board_type = db.query(q)
    q = 'SELECT * FROM io_type ORDER BY id '
    io_type = db.query(q)
    q = 'SELECT * FROM board WHERE enable=1 ORDER BY id'
    all_board = db.query(q)
    q = 'SELECT * FROM area ORDER BY id'
    area = db.query(q)
    d.initialize()  # reload database

    icon = d.A['icon']

    return render_template("setup_board_io.html", msg=msg, msg_type=msg_type, data=res, board=board, board_type=board_type, io_type=io_type, all_board=all_board, area=area, icon=icon)


@app.route('/setup_io_type', methods=["GET", "POST"])
def setup_io_type():
    permission = checkPermission(2)  # check login and privilege
    if permission: return redirect(url_for(permission))

    if request.method == "POST":
        f = request.form
        db.setForm('UPDATE', f.to_dict(), 'io_type')
    q = 'SELECT * FROM io_type ORDER BY type, id'
    res = db.query(q)
    return render_template("setup_io_type.html", data=res)


@app.route('/setup_program', methods=["GET", "POST"])
def setup_program():
    permission = checkPermission(2)  # check login and privilege
    if permission: return redirect(url_for(permission))

    setLog()

    if request.method == "POST" and 'btn' in request.form.to_dict() and (request.form.to_dict()['btn'] == 'Save' or request.form.to_dict()['btn'] == 'Copy'):
        print('Save or New Program Form')
        f = request.form.to_dict()
        # print f
        ch = ''
        chrono = ''
        timer = ''
        x = 1
        for k in sorted(f):  # get chrono information
            if k.find('chrono') >= 0 and f[k] >= '0':
                ch = ch + "{}-".format(f[k])
                if x == 8:
                    chrono = '{}{};'.format(chrono, ch[:-1])
                    ch = ''
                    x = 0
                x = x + 1
        # print(chrono)
        for k in sorted(f):  # get timer information
            if k.find('timer') >= 0 and f[k] >= 0:
                timer = timer + "{}-".format(f[k])
        chrono = chrono[:-1]
        timer = timer[:-1]
        inverted = '1' if 'inverted' in f else '0'
        enable = '1' if 'enable' in f else '0'
        # print timer
        if request.form.to_dict()['btn'] == 'Save':
            q = 'UPDATE program SET in_id="{}", inverted="{}", out_id="{}", type_id="{}", name="{}",'\
                'description="{}", enable="{}", timer="{}", chrono="{}" WHERE id="{}" '\
                .format(f['in_id'], inverted, f['out_id'], f['type_id'], f['name'], f['description'], enable, timer, chrono, f['id'])
        elif request.form.to_dict()['btn'] == 'Copy':
            q = 'INSERT INTO program (in_id, inverted, out_id, type_id, name, description, enable, timer, chrono)'\
                'VALUES("{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}")'.format(f['in_id'], inverted, f['out_id'], f['type_id'], f['name'], f['description'], enable, timer, chrono)
        print q
        db.query(q)
        d.initialize()
        # d.loop()

    elif request.method == "POST" and 'btn' in request.form.to_dict() and request.form.to_dict()['btn'] == 'Delete':
        print('Delete Program Form')
        f = request.form.to_dict()
        q = 'DELETE FROM program WHERE id="{}" '.format(f['id'])
        # print(q)
        db.query(q)
        d.initialize()

    elif request.method == "POST" and [s for s in request.form.to_dict() if "delete_chrono" in s]:
        print('Delete Chrono in Program Form')
        f = request.form.to_dict()
        chronoid = [s for s in request.form.to_dict() if "delete_chrono" in s]
        chronoid = int(chronoid[0][13:])  # chrono part to remove
        q = 'SELECT chrono FROM program WHERE id = "{}"'.format(f['id'])
        chrono = str(db.query(q)[0]['chrono'])
        chrono = chrono.split(';')  # from string to list
        chrono.pop(chronoid - 1)  # remove part of chrono
        chrono = ';'.join(chrono)  # convert list to string
        q = 'UPDATE program SET chrono="{}" WHERE id="{}"'.format(chrono, f['id'])
        db.query(q)
        d.initialize()
    q = 'SELECT * FROM program'
    res = db.query(q)
    timer = res[0]['timer'].split('-')
    chrono = res[0]['chrono'].split(';')
    cr = []  # chrono list
    for c in chrono:
        cr.append(c.split('-'))
    q = 'SELECT bi.* FROM board_io bi, io_type it WHERE bi.io_type_id=it.id AND it.type=1 AND  bi.enable=1 '
    board_io_in = db.query(q)
    q = 'SELECT bi.* FROM board_io bi, io_type it WHERE bi.io_type_id=it.id AND it.type=0 AND  bi.enable=1 '
    board_io_out = db.query(q)
    print(board_io_out)
    q = 'SELECT * FROM program_type'
    program_type = db.query(q)
    return render_template("setup_program.html", data=res, board_io_in=board_io_in, board_io_out=board_io_out, program_type=program_type, timer=timer, chrono=cr)


@app.route('/message')
def message():
    return render_template("message.html")


@app.route('/log')
def log():
    permission = checkPermission(2)  # check login and privilege
    if permission: return redirect(url_for(permission))

    q = 'SELECT * FROM log ORDER BY timestamp desc'
    res = db.query(q)
    q = 'SELECT count(ip) as count, ip FROM log GROUP BY ip ORDER BY count(ip) DESC'
    res1 = db.query(q)
    # print res1
    return render_template("log.html", res=res, res1=res1)


@app.route('/doc')
def doc():
    setLog()
    return render_template("doc.html")


@app.route("/")
@app.route('/home')
def home():
    setLog()
    return render_template("home.html")


@app.route('/welcome')
def welcome():
    return render_template('welcome.html')


@app.route('/hello')
def hello():
    return render_template("hello.html")


@app.route("/setup_user", methods=["GET", "POST"])
def setup_user():
    permission = checkPermission(2)  # check login and privilege
    if permission: return redirect(url_for(permission))

    setLog()

    # userEdit = variabile dell'utente che deve essere modificato
    # sesseion['userEdit'] = variabile di sessione
    f = request.form
    msg = msg_type = ''
    if request.method == "POST" and 'submit' in f and f['submit'] == 'Save':
        if len(f['password']) <= 2 or f['password'] != f['passwordRetype']:  # Check if psw is too short
            msg = "Password too short or not equal!"
            msg_type = 'danger'
            userEdit = session['userEdit']
        else:
            pLog = 1 if 'pLog' in f else 0
            pViewer = 2 if 'pViewer' in f else 0
            pSetup = 4 if 'pSetup' in f else 0
            pAdmin = 128 if 'pAdmin' in f else 0

            # Check if there are at least ONE ADMINISTRATOR
            if int(pAdmin) == 0:
                q = 'SELECT privilege FROM user'
                res = db.query(q)
                priv = 0
                for r in res:
                    print int(r['privilege'])
                    if int(r['privilege']) & 128 > 0:
                        priv += 1
                print priv, session['privilege'], int(session['privilege']) >= 128
                if int(session['privilege']) >= 128 and priv < 2:  # Si sta modificando un Administrator
                    msg = 'There is be at least one administrator user!'
                    msg_type = 'danger'
                    pAdmin = 128

            privilege = pLog + pViewer + pSetup + pAdmin  # calculates privileges to insert into database
            q = 'UPDATE user SET id=%i, username="%s", password="%s", name="%s", surname="%s", lang="%s", session="%i", description="%s", privilege="%i", timestamp="%s" WHERE id=%i'\
                % (int(f['user_id']), f['username'], f['password'], f['name'], f['surname'], f['lang'], int(f['sessiontime']), f['description'], privilege, now(), int(f['user_id']))
            db.query(q)

            # reload session privilege when user is changed
            if int(session['user_id']) == int(f['user_id']):
                session['user_name'] = f['name']
                session['user_id'] = f['user_id']
                session['userEdit'] = f['user_id']
                session['privilege'] = privilege
                session['timestamp'] = now()
                session['sessionTimeout'] = f['sessiontime']

            userEdit = session['userEdit'] = f['user_id']
            msg = 'User save!' if not msg else msg
            msg_type = 'success' if not msg_type else msg_type

    elif 'submit' in f and f['submit'] == 'Edit':  # If other user
        session['userEdit'] = f['users']
        userEdit = session['userEdit']
        msg = 'User edit!'
        msg_type = 'info'
    elif 'submit' in f and f['submit'] == 'Delete':  # Delete other user
        if int(session['user_id']) == int(f['users']):
            msg = 'You are logged and cannot autoremove!'
            msg_type = 'warning'
        else:
            q = 'DELETE FROM user WHERE id = %s' % (f['users'])
            db.query(q)
            msg = 'User Delete!'
            msg_type = 'success'
        userEdit = f['user_id']
    elif 'submit' in f and f['submit'] == 'New':  # Create new user
        q = 'INSERT INTO user ("username","name","surname","password","privilege","session","lang") VALUES ("-","-","-","-","0000","300","en")'
        userEdit = db.query(q)
        msg = 'New User!'
        msg_type = 'info'
        print "NEW USER userEdit", userEdit
    else:
        userEdit = session['user_id']
        msg = 'User edit!'
        msg_type = 'warning'

    q = 'SELECT * FROM user WHERE id = {}'.format(userEdit)  # get current user information
    db_user = db.query(q)[0]
    userPr = int(db_user['privilege'])

    q = 'SELECT * FROM privilege'  # get privilege
    db_privilege = db.query(q)

    if 'privilege' in session and int(session['privilege']) & 128 > 0:
        q = 'SELECT * FROM user WHERE id != {}'.format(userEdit)  # get all users information
        db_users = db.query(q)
    else:
        db_users = [{}]

    print userEdit, userPr & 1, userPr & 2, userPr & 4, userPr & 128, session['privilege']
    return render_template(
        "setup_user.html", user=db_user, privilege=db_privilege, pLog=userPr & 1 > 0, pViewer=userPr & 2 > 0,
        pSetup=userPr & 4 > 0, pAdmin=userPr & 128 > 0, users=db_users, sessionPrivilege=int(session['privilege']), msg_type=msg_type, msg=msg
    )


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.clear()
    # flash('You are logged out')
    return redirect(url_for('login'))


@app.route("/login", methods=["GET", "POST"])
def login():
    setLog()

    f = request.form
    if request.method == "POST" and f['submit'] == 'Enter':
        if len(f['password']) < 3 or len(f['username']) < 3:  # Check if password is too short
            error = "Password to much short"
            return render_template("login.html", error=error)

        q = 'SELECT * FROM user WHERE username = "{}" AND password = "{}"' \
            .format(f['username'], f['password'])
        res = db.query(q)
        if res and len(res[0]) > 0:
            session['logged_in'] = True
            session['user_name'] = res[0]['name']
            session['user_id'] = res[0]['id']
            session['userEdit'] = res[0]['id']
            session['privilege'] = res[0]['privilege']
            session['timestamp'] = now()
            session['sessionTimeout'] = res[0]['session']
            return render_template("hello.html", error='')
        else:
            msg = 'IOValid password or username. Please retry!'
            msg_type = 'warning'
            return render_template("login.html", msg=msg, msg_type=msg_type)
            session['logged_in'] = None
            session.clear()
    else:
        msg = 'Please enter Username and Password!'
        msg_type = 'info'
        return render_template("login.html", msg=msg, msg_type=msg_type)


@app.errorhandler(404)
def page_not_found(e):
    print("Error {}".format(e))
    return render_template('error_page.html', error=e), 404


@app.errorhandler(500)
def internal_server_error(e):
    print("Error {}" .format(e))
    return render_template('error_page.html', error=e), 500

def getIO(start='y'):  # To update board IO values

    try:
        timebegin = now()
        # print "\n------------------------"
        d.getIO()
        # print "getIO ==>> ", now() - timebegin
    except:
        print('Error Domocontrol.py getIn')
        traceback.print_exc()
    if start == 'y':
        threading.Timer(1, getIO).start()
    else:
        threading.Timer(1, getIO).cancel()

def setProg(start='y'):  # To update Program
    try:
        timebegin = now()
        d.setProg()
        # print "setProg ==>> ", now() - timebegin
    except:
        print('Error Domocontrol.py setProg')
        traceback.print_exc()
    if start == 'y':
        threading.Timer(1, setProg).start()
    else:
        threading.Timer(1, setProg).cancel()

if __name__ == '__main__':
    getIO()
    setProg()

    app.debug = 1
    socketio.run(app, port=8000, host='0.0.0.0')

    print "FINE"
