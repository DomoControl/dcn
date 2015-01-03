#!/usr/bin/python 
from flask import *
from db import Database
import sys
import datetime
#~ import time
import domocontrol
#~ import threading
from flask.ext.babel import Babel
from config import LANGUAGES
#~ from apscheduler.schedulers.blocking import BlockingScheduler

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.config.from_object('config')
babel = Babel(app)

DATABASE = '/home/pi/dcn/db/db.sqlite'
db = Database(dbname=DATABASE) #metodi per database
d = domocontrol.Domocontrol()

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

def now():
    return datetime.datetime.now()



def setLog(): #Da finire. Serve per tracciare l'IP
    userAgentString = request.headers.get('User-Agent')
    res = db.query("INSERT INTO log (command,ip) VALUES('%s', '%s')" %(request.url,request.remote_addr))
        
@app.route('/setup_area', methods=["GET","POST"])
def setup_area():
    if request.method == "POST":
        f = request.form #get inpput value
        db.setForm('UPDATE', f.to_dict(), 'area') #recall db.setForm to update query. UPDATE=Update method, f.to_dict=dictionary with input value, area:database table
    q = 'SELECT * FROM area'
    res = db.query(q)
    return render_template("setup_area.html", data=res)

@app.route('/setup_privilege', methods=["GET","POST"])
def setup_privilege():
    if request.method == "POST":
        f = request.form
        db.setForm('UPDATE', f.to_dict(), 'privilege')
    q = 'SELECT * FROM privilege'
    res = db.query(q)
    return render_template("setup_privilege.html", data=res)

@app.route('/setup_translation', methods=["GET","POST"])
def setup_translation():
    if request.method == "POST":
        f = request.form
        q = 'UPDATE translation SET en="%s", it="%s", de="%s" WHERE id="%s" ' %(f["en"], f["it"], f["de"], f["id"])
        db.query(q)
    q = 'SELECT * FROM translation'
    res = db.query(q)
    return render_template("setup_translation.html", data=res)

@app.route('/setup_board_type', methods=["GET","POST"])
def setup_board_type():
    if request.method == "POST":
        f = request.form
        db.setForm('UPDATE', f.to_dict(), 'board_type')
    q = 'SELECT * FROM board_type'
    
    res = db.query(q)
    return render_template("setup_board_type.html", data=res)

@app.route('/setup_board', methods=["GET","POST"])
def setup_board():
    if request.method == "POST":
        f = request.form
        if f['submit'] == 'Save':
            if 'enable' in f:
                enable=1
            else:
                enable=0
            q = 'UPDATE board SET id="%s", name="%s", description="%s", enable="%s", address="%s", board_type="%s" WHERE id="%s"' %(f["id"], f["name"], f["description"], enable, f["address"], f["board_type"], f["id"]) 
            db.query(q)
            q = 'SELECT * FROM board'
            res = db.query(q)
            q = 'SELECT * FROM board_type ORDER BY id'
            board_type = db.query(q)
            return render_template("setup_board.html", data=res, board_type=board_type)
        elif f['submit'] == 'Edit IO':
            return redirect( url_for('.setup_board_io', id=f['id']) )
    else:        
        q = 'SELECT * FROM board'
        res = db.query(q)
        q = 'SELECT * FROM board_type ORDER BY id'
        board_type = db.query(q)
        return render_template("setup_board.html", data=res, board_type=board_type)
            
@app.route('/setup_board_io', methods=["GET","POST"])
def setup_board_io():
    if request.method == "POST":
        f = request.form
        print(f)
        if f['submit'] == 'Save':
            if 'enable' in f:
                enable=1
            else:
                enable=0
            q = 'UPDATE board_io SET id="%s", io_type_id="%s", name="%s", description="%s", enable="%s", board_id="%s", address="%s" WHERE id="%s"' \
                %(f["id"], f['io_type_id'], f["name"], f["description"], enable, f['board_id'], f["address"], f["id"]) 
            db.query(q)
        elif f['submit'] == 'Add IO':
            if 'enable' in f:
                enable=1
            else:
                enable=0
            q = 'INSERT INTO board_io (io_type_id, name, description, enable, board_id, address) VALUES ("%s", "%s", "%s", "%s", "%s", "%s")' \
                %(f['io_type_id'], f["name"], f["description"], enable, f['board_id'], f["address"]) 
            db.query(q)
        elif f['submit'] == 'Delete':
            q = "DELETE FROM board_io WHERE id=%s" %f['id']
            db.query(q)
        
    id = request.args['id']
    q = 'SELECT * FROM board_io WHERE board_id=%s' %id
    res = db.query(q)
    q = 'SELECT * FROM board WHERE id=%s' %id
    board = db.query(q)
    q = 'SELECT * FROM board_type WHERE id=%s' %board[0]['board_type']
    board_type = db.query(q)
    q = 'SELECT * FROM io_type'
    io_type = db.query(q)
    q = 'SELECT * FROM board'
    all_board = db.query(q)
    return render_template("setup_board_io.html", data=res, board=board, board_type=board_type, io_type=io_type, all_board=all_board)

@app.route('/setup_io_type', methods=["GET","POST"])
def setup_io_type():
    if request.method == "POST":
        f = request.form
        db.setForm('UPDATE', f.to_dict(), 'io_type')
    q = 'SELECT * FROM io_type'
    
    res = db.query(q)
    return render_template("setup_io_type.html", data=res)

@app.route('/setup_program_type', methods=["GET","POST"])
def setup_program_type():
    if request.method == "POST":
        f = request.form
        db.setForm('UPDATE', f.to_dict(), 'program_type')
    q = 'SELECT * FROM program_type'
    
    res = db.query(q)
    return render_template("setup_program_type.html", data=res)

@app.route('/setup_program', methods=["GET","POST"])
def setup_program():
    setLog()
    #Test is user is logged
    if not 'logged_in' in session and session['logged_in']==True:
        return render_template("login.html") 
    
    if request.method == "POST" and 'btn' in request.form.to_dict() and (request.form.to_dict()['btn']=='Save' or request.form.to_dict()['btn']=='New'):
        print('Save or New Program Form')
        f = request.form.to_dict()
        print f
        ch = ''
        chrono = ''
        timer = ''
        x = 1
        for k in sorted(f): #get chrono information
            if k.find('chrono') >= 0 and f[k] >= '0':
                ch = ch+"%s-" %f[k]
                if x == 8:
                    chrono = chrono + ch[:-1] + ";"
                    ch = ''
                    x = 0
                x = x+1
        print(chrono)
        
        for k in sorted(f): #get timer information
            if k.find('timer') >= 0 and f[k] >= 0:
                timer = timer+"%s-" %f[k] 
        chrono =  chrono[:-1]
        timer = timer[:-1]
                    
        inverted = '1' if 'inverted' in f else '0'
        enable = '1' if 'enable' in f else '0'
        
        if request.form.to_dict()['btn']=='Save':
            q = 'UPDATE program SET in_id="%s", delay="%s", inverted="%s", out_id="%s", type_id="%s", name="%s", description="%s", enable="%s", timer="%s", chrono="%s" WHERE id="%s"  ' \
                %(f['in_id'], f['delay'], inverted, f['out_id'], f['type_id'], f['name'], f['description'], enable, timer, chrono, f['id'])
        elif request.form.to_dict()['btn']=='New':
            q = 'INSERT INTO program (in_id, delay, inverted, out_id, type_id, name, description, enable, timer, chrono) VALUES( "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s" )' \
                %(f['in_id'], f['delay'], inverted, f['out_id'], f['type_id'], f['name'], f['description'], enable, timer, chrono)
        
        print(q)
        db.query(q)
        
    elif request.method == "POST" and 'btn' in request.form.to_dict() and request.form.to_dict()['btn']=='Delete':
        print('Delete Program Form')
        f = request.form.to_dict()
        print(f['id'])   
    
    elif request.method == "POST" and [s for s in request.form.to_dict() if "delete_chrono" in s]:
        print('Delete Chrono in Program Form')
        f = request.form.to_dict()
        chronoid = [s for s in request.form.to_dict() if "delete_chrono" in s] 
        chronoid = int(chronoid[0][13:]) #chrono part to remove 
        q = 'SELECT chrono FROM program WHERE id="%s"' %f['id']
        chrono = str(db.query(q)[0]['chrono'])
        chrono = chrono.split(';') #from string to list
        chrono.pop(chronoid-1) #remove part of chrono
        chrono = ';'.join(chrono) #convert list to string
        q = 'UPDATE program SET chrono="%s" WHERE id="%s" ' %(chrono, f['id'])
        db.query(q)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
    q = 'SELECT * FROM program'
    res = db.query(q)
    timer=res[0]['timer'].split('-')
    chrono=res[0]['chrono'].split(';')
    cr = [] #chrono list
    for c in chrono:
        cr.append(c.split('-'))
    q = 'SELECT * FROM board_io'
    board_io = db.query(q)
    q = 'SELECT * FROM program_type'
    program_type = db.query(q)
    
    return render_template("setup_program.html", data=res, board_io=board_io, program_type=program_type,timer=timer, chrono=cr )

@app.route('/message')
def message():
    return render_template("message.html")

@app.route('/_add_numbers')
def add_numbers():
    a = request.args.get('a', 0, type=int)
    b = request.args.get('b', 0, type=int)
    print( a, b)
    return jsonify(result=a + b)




@app.route('/log')
def log():
    q = 'SELECT * FROM log ORDER BY timestamp desc'
    res = db.query(q)
    return render_template("log.html", res=res)

@app.route('/doc')
def doc():   
    setLog() 
    return render_template("doc.html")


@app.route('/setup_user', methods=["GET","POST"])
def setup_user():
    setLog()
    error = ''
    if request.method == "POST":
        #save form data
        if request.form["password"] != request.form["retype_password"]: #check password and retype_password
            error = "Password not equal"
        else:
            #get privilege
            x=0
            privilege = ''
            while x<10:
                try:
                    privilege = privilege + request.form['privilege[%i]' %x] + ";"
                except:
                    pass
                x = x+1
            
            q = 'UPDATE user SET id="%s", username="%s", name="%s", surname="%s", password="%s", session="%s", lang="%s", privilege="%s", timestamp="%s" WHERE id="%s" ' \
                %(request.form["id"], request.form["username"], request.form["name"], request.form["surname"], request.form["password"], request.form["session"], \
                request.form["lang"], privilege[:-1], now(), request.form["id"]    )
            #~ print q
            db.query(q)
            
    #read data
    if 'logged_in' in session and session['logged_in']==True:
        #~ flash('New entry was successfully posted')
        q = 'SELECT * FROM user WHERE id=%s' %session['user_id']
        user = db.query(q)[0]
        q ='SELECT * FROM privilege'
        privilege = db.query(q)
        return render_template("setup_user.html", user=user, privilege=privilege, error=error )
    else:
        return render_template("login.html")


@app.route("/")
@app.route('/home')
def home():
    setLog()
    return render_template("home.html")
    
@app.route('/status')
def status():   
    setLog()
    if 'logged_in' in session and session['logged_in']==True:
        q = 'SELECT * FROM program'
        res = db.query(q)
        for r in res:
            print r
        
        
    
    
        return render_template("status.html")
    else:
        return render_template("login.html")   


@app.route('/welcome')
def welcome():
    return render_template('welcome.html')
    
@app.route('/hello')
def hello():
    session['ciccio'] = 'user_name'
    print(session.get('ciccio'))
    return render_template("hello.html")
    
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You are logged out')
    return redirect (url_for('login'))

@app.route("/login", methods=["GET","POST"])    
def login():
    setLog()
    error = None
    if request.method == "POST":
        q = 'SELECT * FROM user WHERE username = "%s" AND password = "%s"' %(request.form["username"],request.form["password"])
        res = db.query(q)
        if res and len(res[0]) > 0:
            session['logged_in'] = True
            session['user_name'] = res[0]['name']
            session['user_id'] = res[0]['id']
            return render_template("hello.html", error=error)
        else:
            session['logged_in'] = None
            error = "invalid password or username. Please retry"
    return render_template("login.html", error=error)



if __name__ == '__main__':       
    
    app.run(
        host="0.0.0.0", 
        port=int("5000"), 
        debug=True
    )

