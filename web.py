#!/usr/bin/python
from flask import Flask, request, render_template, g, session, jsonify, redirect, url_for
from flask.ext.bootstrap import Bootstrap
from db import Database
import sys
#~ import datetime
from date import now #get time function
import threading
import domocontrol
from flask.ext.babel import Babel
from config import LANGUAGES
import time
import copy

print("Begin")

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.config.from_object('config')
babel = Babel(app)
bootstrap = Bootstrap(app)
DATABASE = './db/db.sqlite'
db = Database(dbname=DATABASE)  # metodi per database
d = domocontrol.Domocontrol()
P = {}  # Dict with Program
PCopy = {}  #Copy P dictionary
A = {}  # All other db information        
ACopy = {} #Copy A dictionary
IO = {} #Content IO status (menu status)
IOCopy = {} #Copy IO dictionary


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
    #~ if session['privilege']
    userAgentString = request.headers.get('User-Agent')
    res = db.query("INSERT INTO log (command,ip) VALUES('{}', '{}')".format(request.url, request.remote_addr))

# Test is user is logged
def checkLogin():
    #~ print session['sessionTimeout'], (now() - session['timestamp']).total_seconds()
    if 'logged_in' in session and session['logged_in']==True and (now() - session['timestamp']).total_seconds() < session['sessionTimeout']:
        session['timestamp'] = now()
        return 1
    else:
        return 0

@app.route('/no_permission')
def no_permission(error=''):
    return render_template("no_permission.html", error=error)

@app.route('/getTime')  # return datetime now() to show in footer
def getTime():
    return jsonify(result=now().strftime("%a %d/%m/%y  %H:%M"))

@app.route('/menu_status')
def menu_status():
    if not checkLogin(): return redirect(url_for('logout'))
    if int(session['privilege'][0:1]) == 0 and int(session['privilege'][1:2]) == 0:
        error='Insufficient privilege for Setup Status Menu!'
        return render_template( "no_permission.html", error=error)
    setLog()
    return render_template("menu_status.html")

@app.route('/getStatus', methods=["GET", "POST"])
def getStatus():  # return array with all data informations only if required
    if request.args['reloadDictA'] == 'true':
        A = d.getDict('A',reloadDict=True)
    else:
        A = d.getDict('A')
    
    if request.args['reloadDictIO'] == 'true':
        IO = d.getDict('IO',reloadDict=True)
    else:
        IO = d.getDict('IO')
        
    #~ print A,IO
    return jsonify(resultIO=IO,resultA=A)

@app.route('/getProgramStatus', methods=["GET", "POST"])
def getProgram(reloadDict=False):  # return array with all program informations
    global PCopy
    if reloadDict == True:
        request.args['reloadDictA'] == 'true'
        request.args['reloadDictP'] == 'true'
        
    if request.args['reloadDictA'] == 'true':
        A = d.getDict('A',reloadDict=True)
    else:
        A = d.getDict('A')
        
    if request.args['reloadDictP'] == 'true':
        P = d.getDict('P',reloadDict=True)
    else:
        P = d.getDict('P')
        
    #~ print P,A
    return jsonify(resultP=P, resultA=A)

@app.route('/setIN', methods=['GET', 'POST'])
def setIN():
    pid = request.args.get('id')  # Program id
    # print pid
    mode = request.args.get('mode')  # to set IN = mode
    print("Set Button", pid, mode)
    d.setIN(pid, mode)
    d.loop()
    #~ getProgram(reloadDict=True)
    return jsonify(result=123)


@app.route("/setup_user", methods=["GET", "POST"])
def setup_user():
    if not checkLogin(): return redirect(url_for('logout')) #Test if user is logged
    error=''
    if int(session['privilege'][0:1]) == 0:
        error='Insufficient privilege for Setup User Menu!'
        return render_template( "no_permission.html", error=error)
        
    setLog()

    f = request.form
    if request.method == "POST" and 'submit' in f and f['submit'] == 'Save':
        if len(f['password']) <=2 or f['password'] != f['passwordRetype']:
            error = "Password non impostata o non coincidenti"
        else:
            privilegeLog = 1 if 'privilegeLog' in f else '0'
            privilegeViewer = 1 if 'privilegeViewer' in f else '0'
            privilegeSetup = 1 if 'privilegeSetup' in f else '0'
            privilegeAdmin = 1 if 'privilegeAdmin' in f else '0'
            
            #Check if there are at least ONE ADMINISTRATOR
            if int(privilegeAdmin) == 0:
                q = 'SELECT privilege FROM user'
                res = db.query(q)
                priv = 0
                for r in res:
                    if r['privilege'][0:1] == '1':
                        priv += 1
                if priv == 1:
                    error = 'There must be at least one administrator user!'
                    privilegeAdmin = 1
            
            privilege = "{}{}{}{}".format(privilegeAdmin,privilegeSetup,privilegeViewer,privilegeLog) 
            q='UPDATE user SET id=%s, username="%s", password="%s", name="%s", surname="%s", lang="%s", session="%s", description="%s", privilege="%s", timestamp="%s" WHERE id=%s'\
            %(f['user_id'],f['username'],f['password'],f['name'],f['surname'],f['lang'],f['sessiontime'],f['description'],privilege,now(),f['user_id'])
            db.query(q)
            
            #reload session privilege when user is changed
            if int(session['user_id']) == int(f['user_id']):
                session['user_name'] = f['name']
                session['user_id'] = f['user_id']
                session['privilege'] = privilege
                session['timestamp'] = now()
                session['sessionTimeout'] = f['sessiontime']                
                return redirect(url_for('setup_user'))
    try:
        if f['submit'] == 'Edit':
            user_id = f['users']
        elif f['user_id']:
            user_id=f['user_id']
        else:
            user_id = session['user_id']
        if f['submit'] == 'Delete':
            q='DELETE FROM user WHERE id=%s' %(f['users'])
            db.query(q)
        if f['submit'] == 'New':
            q='INSERT INTO user ("username","name","surname","password","privilege","session","lang") VALUES ("prova","prova","prova","prova","0000","300","en")'
            user_id = db.query(q)
    except:
        pass
    try:
        print user_id
    except:
        user_id = session['user_id']
    q = 'SELECT * FROM user WHERE id={}'.format(user_id)
    user = db.query(q)[0]
    q = 'SELECT * FROM privilege'
    privilege = db.query(q)
    q = 'SELECT * FROM user WHERE id !={}'.format(user_id)
    users = db.query(q)
    return render_template( "setup_user.html", user=user, privilege=privilege, error=error, users=users)


@app.route('/setup_area', methods=["GET", "POST"])
def setup_area():
    #Test if user is logged
    if not checkLogin(): return redirect(url_for('logout'))
    if request.method == "POST":
        f = request.form  # get input value
        db.setForm('UPDATE', f.to_dict(), 'area')  # recall db.setForm to update query. UPDATE=Update method, f.to_dict=dictionary with input value, area:database table
    q = 'SELECT * FROM area'
    res = db.query(q)
    return render_template("setup_area.html", data=res)
    
@app.route('/menu_sensor', methods=["GET", "POST"])
def menu_sensor(chartID = 'chart_ID', chart_type = 'line', chart_height = 350):
	#Test if user is logged
    if not checkLogin(): return redirect(url_for('login'))
    
    q = 'SELECT * FROM sensor WHERE type=1 ORDER BY datetime DESC LIMIT 248'
    temperature = db.query(q)
    temp = []
    categories = []
    for t in temperature:
        micros = float(time.mktime(time.strptime(t['datetime'], '%Y-%m-%d %H:%M:%S'))*1000) 
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
    
    chart = {"renderTo": chartID, "type": chart_type, "height": chart_height,}
    
    series = [{"yAxis":0, "name": 'Temperature', "data": temp}, {"yAxis":1, "name":'Humidity', "data":hum} ]
    tooltip = {"backgroundColor": '#00FFC5', "borderColor": 'black', "borderRadius": 10, "borderWidth": 3}
    title = {"text": 'Temperature / Humidity'}
    xAxis = {"title": {"text": 'Date'}, "type":'datetime', "categories":categories, "dateTimeLabelFormats": { "month": '%e. %b', "year": '%b' }, "tickPixelInterval": 20}
    
    yAxis = [{"title": {"text": 'Temperature'}},{"title": {"text": 'Humidity'}, "opposite":'true'}]
    tooltip = { "headerFormat": '<b>{series.name}</b><br>', "pointFormat": '{point.x:%e. %b}: {point.y:.2f} m' }
    
    return render_template('menu_sensor.html', chartID=chartID, chart=chart, series=series, title=title, xAxis=xAxis, yAxis=yAxis, tooltip=tooltip) 


@app.route('/setup_privilege', methods=["GET", "POST"])
def setup_privilege():
    #Test if user is logged
    if not checkLogin(): return redirect(url_for('logout'))
    if request.method == "POST":
        f = request.form
        db.setForm('UPDATE', f.to_dict(), 'privilege')
    q = 'SELECT * FROM privilege'
    res = db.query(q)
    return render_template("setup_privilege.html", data=res)


@app.route('/setup_translation', methods=["GET", "POST"])
def setup_translation():
    #Test if user is logged
    if not checkLogin(): return redirect(url_for('logout'))
    if request.method == "POST":
        f = request.form
        q = 'UPDATE translation SET en="{}", it="{}", de="{}" WHERE id="{}" '.format(f["en"], f["it"], f["de"], f["id"])
        db.query(q)
    q = 'SELECT * FROM translation'
    res = db.query(q)
    return render_template("setup_translation.html", data=res)


@app.route('/setup_board_type', methods=["GET", "POST"])
def setup_board_type():
    #Test if user is logged
    if not checkLogin(): return redirect(url_for('logout'))
    if request.method == "POST":
        f = request.form
        db.setForm('UPDATE', f.to_dict(), 'board_type')
    q = 'SELECT * FROM board_type'
    res = db.query(q)
    return render_template("setup_board_type.html", data=res)


@app.route('/setup_board', methods=["GET", "POST"])
def setup_board():
    #Test if user is logged
    if not checkLogin(): return redirect(url_for('logout'))
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

def checkEnable(id, enable=0):
    if enable == 1:
        return 1
    P = d.P
    A = d.A
    io_type_id = A['board_io'][int(id)]['io_type_id']
    if A['io_type'][io_type_id]['type'] == 0:
        type = 'out_id'
    else:
        type = 'in_id'
    
    for r in P:
        print P[r][type], id
        if int(P[r][type]) == int(id):
            print "ERROR**************************"
    return 0
        

@app.route('/setup_board_io', methods=["GET", "POST"])
def setup_board_io():
    #Test if user is logged
    if not checkLogin(): return redirect(url_for('logout'))
    error=''
    if request.method == "POST":
        f = request.form
        print(f)
        if f['submit'] == 'Save':
            if 'enable' in f:
                enable = 1
            else:
                enable = 0
            
            if checkEnable(f["id"], enable) == 0:
                error='Cannot disable I/O used in Program, first change Program '
            else:
                q = 'UPDATE board_io SET id="{}", io_type_id="{}", name="{}", description="{}", area_id="{}", enable="{}", board_id="{}", address="{}" WHERE id="{}"'\
                .format(f["id"], f['io_type_id'], f["name"], f["description"], f["area_id"], enable, f['board_id'], f["address"], f["id"])
                db.query(q)
        elif f['submit'] == 'Add IO':
            if 'enable' in f:
                enable = 1
            else:
                enable = 0
            q = 'INSERT INTO board_io (io_type_id, name, description, area_id, enable, board_id, address) VALUES ("{}", "{}", "{}", "{}", "{}", "{}", "{}")'\
            .format(f['io_type_id'], f["name"], f["description"], f["area_id"], enable, f['board_id'], f["address"])
            db.query(q)
        elif f['submit'] == 'Delete':
            if checkEnable(f["id"]) == 0:
                error='Cannot delete I/O used in Program, first change Program '
            else:
                q = "DELETE FROM board_io WHERE id={}".format(f['id'])
                db.query(q)
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
    d.setup() #reload database
    return render_template("setup_board_io.html", error=error, data=res, board=board, board_type=board_type, io_type=io_type, all_board=all_board, area=area)


@app.route('/setup_io_type', methods=["GET", "POST"])
def setup_io_type():
    #Test if user is logged
    if not checkLogin(): return redirect(url_for('logout'))
    if request.method == "POST":
        f = request.form
        db.setForm('UPDATE', f.to_dict(), 'io_type')
    q = 'SELECT * FROM io_type ORDER BY type, id'
    res = db.query(q)
    return render_template("setup_io_type.html", data=res)


@app.route('/setup_program_type', methods=["GET", "POST"])
def setup_program_type():
    #Test if user is logged
    if not checkLogin(): return redirect(url_for('logout'))
    if request.method == "POST":
        f = request.form
        db.setForm('UPDATE', f.to_dict(), 'program_type')
    q = 'SELECT * FROM program_type'
    res = db.query(q)
    return render_template("setup_program_type.html", data=res)


@app.route('/setup_program', methods=["GET", "POST"])
def setup_program():
    #Test if user is logged
    if not checkLogin(): return redirect(url_for('logout'))
    setLog()
    # Test is user is logged
    if not 'logged_in' in session and session['logged_in'] == True:
        return render_template("login.html")
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
        #~ print timer
        if request.form.to_dict()['btn'] == 'Save':
            q = 'UPDATE program SET in_id="{}", inverted="{}", out_id="{}", type_id="{}", name="{}",'\
            'description="{}", enable="{}", timer="{}", chrono="{}" WHERE id="{}" '\
            .format(f['in_id'], inverted, f['out_id'], f['type_id'], f['name'], f['description'], enable, timer, chrono, f['id'])
        elif request.form.to_dict()['btn'] == 'Copy':
            q = 'INSERT INTO program (in_id, inverted, out_id, type_id, name, description, enable, timer, chrono)'\
            'VALUES("{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}")'.format(f['in_id'], inverted, f['out_id'], f['type_id'], f['name'], f['description'], enable, timer, chrono)
        #~ print q
        db.query(q)
        d.loop()

    elif request.method == "POST" and 'btn' in request.form.to_dict() and request.form.to_dict()['btn'] == 'Delete':
        print('Delete Program Form')
        f = request.form.to_dict()
        q = 'DELETE FROM program WHERE id="{}" '.format(f['id'])
        #~ print(q)
        db.query(q)
        d.setup()

    elif request.method == "POST" and [s for s in request.form.to_dict() if "delete_chrono" in s]:
        print('Delete Chrono in Program Form')
        f = request.form.to_dict()
        chronoid = [s for s in request.form.to_dict() if "delete_chrono" in s]
        chronoid = int(chronoid[0][13:])  # chrono part to remove
        q = 'SELECT chrono FROM program WHERE id="{}"'.format(f['id'])
        chrono = str(db.query(q)[0]['chrono'])
        chrono = chrono.split(';')  # from string to list
        chrono.pop(chronoid-1)  # remove part of chrono
        chrono = ';'.join(chrono)  # convert list to string
        q = 'UPDATE program SET chrono="{}" WHERE id="{}"'.format(chrono, f['id'])
        db.query(q)
        d.setup()
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
    #Test if user is logged
    if not checkLogin(): return redirect(url_for('logout'))
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

@app.route('/menu_program')
def menu_program():
    #Test if user is logged
    if not checkLogin(): return redirect(url_for('logout'))
    setLog()
    if 'logged_in' in session and session['logged_in'] == True:
        return render_template("menu_program.html")
    else:
        return redirect(url_for('login'))








@app.route('/welcome')
def welcome():
    return render_template('welcome.html')


@app.route('/hello')
def hello():
    return render_template("hello.html")


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.clear()
    #~ flash('You are logged out')
    return redirect(url_for('login'))


@app.route("/login", methods=["GET", "POST"])
def login():
    setLog()
    error=''
    f = request.form
    if request.method == "POST" and f['submit'] == 'Enter':
        if len(f['password']) <=2 or f['username'] <=2:
            error = "Password o Username not valid"
        else:
            q = 'SELECT * FROM user WHERE username = "{}" AND password = "{}"' \
            .format(f['username'], f['password'])
            res = db.query(q)
            if res and len(res[0]) > 0:
                session['logged_in'] = True
                session['user_name'] = res[0]['name']
                session['user_id'] = res[0]['id']
                session['privilege'] = res[0]['privilege']
                session['timestamp'] = now()
                session['sessionTimeout'] = res[0]['session']
                return render_template("hello.html", error=error)
            else:
                session['logged_in'] = None
                #~ print session
                session.clear()
                #~ print session
                error = "invalid password or username. Please retry"
    return render_template("login.html", error=error)

@app.errorhandler(404)
def page_not_found(e):
    print("Error {}".format(e))
    return render_template( 'error_page.html', error=e), 404


@app.errorhandler(500)
def internal_server_error(e):
    print("Error {}" .format(e))
    return render_template('error_page.html', error=e ), 500

def loop():
    timebegin = now()
    try:
        d.loop()
    except:
        print('Error Domocontrol.py')
        

    threading.Timer(1, loop).start()
    print now() - timebegin
    print '-----------------------------------------------------------------'    

if __name__ == '__main__':
    loop()
    try:
        app.run(host="0.0.0.0", port=5000, debug=False)
    except:
    #~ except InvalidCommand as err:
        #~ print("*** Error: {}".format(err))
        pass

