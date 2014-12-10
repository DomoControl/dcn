#!/usr/bin/python
from flask import *
import sys
import datetime
import sqlite3
import smbus as smbus
#~ from flask.ext.babel import gettext, ngettext
#~ from functools import wraps

app = Flask(__name__)
app.secret_key = 'why would I tell you my secret key?'

def now():
    return datetime.datetime.now()

DATABASE = '/home/pi/dcn/db/db.sqlite'

def conn_db():
    return sqlite3.connect(DATABASE)

def query(query, args=(), one=False):
    cur = conn_db()
    res = cur.execute(query, args)
    if query.find('SELECT') > -1:
        rv = [dict((res.description[idx][0], value)
            for idx, value in enumerate(row)) for row in res.fetchall()]
        cur.close()
        return (rv[0] if rv else None) if one else rv
    elif query.find('INSERT') or query.find('UPDATE'):
        a = cur.commit()
        cur.close()

def setLog(): #Da finire. Serve per tracciare l'IP
    userAgentString = request.headers.get('User-Agent')
    #~ print userAgentString
    #~ print dir(request)
    #~ print request.base_url #ritorna l'indirizzo della pagina
    #~ print request.cookies #ritoran i cookies
    #~ print request.headers #ritorna l'indirizzo IP e molto altro
    #~ print request.host #ritorna l'indirizzo chiamato
    #~ print request.remote_addr #ritorna l'indirizzo IP
    #~ print request.remote_user
    q = "INSERT INTO pi_log (command,ip) VALUES('%s', '%s')" %(request.url,request.remote_addr)
    #~ print q
    res = query(q)
    print res

#Search all valid I2C devices and resurn the address
def mapdev():
    device=[]
    for a in range(0,10):
        try:
            i2c = smbus.SMBus(a)
            #~ print 'Device /dev/i2c-x: %s ' %a
            for b in range(1,100):
                try: 
                    i2c.read_byte_data(b,0)
                    device.append({a : b})
                except: 
                    pass
        except:
            pass
    return device
#~ device = mapdev() #ritorna i device e l'indirizzo corrispondente dei dispositivi I2C
#~ print device

def program(x=0):
    i2c = smbus.SMBus(1)
    i2c.write_byte(32,255)
    i2c.write_byte(33,255)
    #~ print help(i2c.read_byte)
    #~ print i2c.read_byte(32)   
    #~ b =   i2c.read_byte(33)
    #~ print 0xb

program(3)
#~ q = 'SELECT * FROM pi_board WHERE board_type=1 AND enable=1'
#~ res = query(q)

def setProgram(): #Put into P dict all pi_program DB
    try:
        print P
    except:
        P = {}
    q = "SELECT * FROM pi_program WHERE enable=1"
    res = query(q)
    P['program'] = {}
    for r in res:
        P['program'].update({r['id'] : r})        
        #~ P['program'][r['id']].update({'OUT' : getIO(P['program'][r['id']]['out_id'])}) #Inizializza valore OUT
        P['program'][r['id']].update({'OUT' : 0})
        P['program'][r['id']].update({'IN_DELAY' : 0})
        P['program'][r['id']].update({'OUT_DELAY' : 0})
        P['program'][r['id']].update({'IN' : r['inverted']})
    #~ debug(P['program'])
    return P
P = setProgram()

def setBoard(): #Setta l'indirizzo delle board
    q = "SELECT id, address, board_type FROM pi_board WHERE address > 0 "
    res = query(q) 
    #~ debug(res)
    P['board'] = {}
    P['pcb'] = {}
    for r in res:
        if r['board_type'] == 1: #Board I2C
            #~ P['board']['board_id'] = {'board' : PCF8574(int(r['board_address']))}
            P['board'].update({r['id'] : r})
            try:
                P['pcb'].update({r['id'] : PCF8574(int(r['address']))})
            except:
                debug('Board %s problem' %r['id'])
            
        elif r['board_type'] == 2: #Board RS485
            pass
        else:
            pass

def setBoardIO():
    q = "SELECT * FROM pi_board_io"
    res = query(q) 
    P['board_io'] = {}
    for r in res:
        P['board_io'].update({r['id'] : r})

    q = "SELECT * FROM pi_board"
    res = query(q) 
    P['board'] = {}
    for r in res:
        P['board'].update({r['id'] : r})

    q = "SELECT * FROM pi_type"
    res = query(q) 
    P['type'] = {}
    for r in res:
        P['type'].update({r['id'] : r})

def getIO(io_id, p_id, All=0): #update IN status in P dict
    
    #~ debug('io_id=%s  p_id=%s all=%s' %(io_id, p_id, All))
    if io_id==0: #IO virtuale
        return
        
    board_id =  P['board_io'][io_id]['board_id']
    io_address = int(P['board_io'][io_id]['address'])
    
    if io_address > 0 : #Board I2C and io = input
        io = P['pcb'][board_id].portRead()
        #~ debug('============>>>>>>>> io=%s' %io)
        if All == 1:
            return io
        else:
            #~ debug("io=%s  M[io_address]=%s  io & M[io_address]=%s " %(io, M[io_address], io & M[io_address]))
            
            P['program'][p_id].update({'IN' : 1 if io & M[io_address] else 0}) 
            
    elif io_address == 0 : #io = input and input = web touch
        if All == 1:
            return None
        pass

def setOUT(io_id, p_id, OUT): #Set OUT status
    #~ debug('setOUT: io_id:%s  p_id:%s  OUT:%s' %(io_id, p_id, OUT))
    if int(P['board_io'][io_id]['address']) == int(0):
        return
    
    board_id =  P['board_io'][io_id]['board_id']
    io_address = int(P['board_io'][io_id]['address'])
    try:
        io_status = P['pcb'][board_id].portRead()
    except:
        io_status = 0
        pass
    
    if OUT == 1:
        out = io_status | M[io_address]
        #~ debug("PRIMA  io_id=%s   p_id=%s  out=%s   OUT=%s   io_status=%s " %(io_id, p_id,  out,  OUT, io_status))
        P['pcb'][board_id].portWrite(out)
        #~ P['program'][p_id].update({'OUT' : '0'})
    elif OUT == 0:
        out = io_status ^ M[io_address] 
        #~ debug("PRIMA  io_id=%s   p_id=%s  out=%s   OUT=%s   io_status=%s " %(io_id, p_id,  out,  OUT, io_status))
        if io_status & M[io_address] > 0:
            P['pcb'][board_id].portWrite(out)
            #~ P['program'][p_id].update({'OUT' : '0'})
        else:
            out = '-'
    #~ debug("DOPO  io_id=%s   p_id=%s  out=%s   OUT=%s   io_status=%s " %(io_id, p_id,  out,  OUT, io_status))
    #~ debug("OUT value (io_id, io_status, io_address, out_value, out):%s  %s  %s  %s  %s" %(io_address, io_status, M[io_address],  OUT, out))





@app.route('/setup_area', methods=["GET","POST"])
def setup_area():    
    q = 'SELECT * FROM pi_area'
    pi_area = query(q)
    return render_template("setup_area.html", pi_area=pi_area)

@app.route('/_add_numbers')
def add_numbers():
    
    a = request.args.get('a', 0, type=int)
    b = request.args.get('b', 0, type=int)
    print a, b
    return jsonify(result=a + b)




@app.route('/log')
def log():
    q = 'SELECT * FROM pi_log ORDER BY timestamp desc'
    res = query(q)
    return render_template("log.html", res=res)

@app.route('/doc')
def doc():   
    setLog() 
    return render_template("doc.html")

@app.route('/setup_program')
def setup_program():
    setLog()
    if 'logged_in' in session and session['logged_in']==True:
        return render_template("setup_program.html")
    else:
        return render_template("login.html")   

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
            
            q = 'UPDATE pi_user SET id="%s", username="%s", name="%s", surname="%s", password="%s", session="%s", lang="%s", privilege="%s", timestamp="%s" WHERE id="%s" ' \
                %(request.form["id"], request.form["username"], request.form["name"], request.form["surname"], request.form["password"], request.form["session"], \
                request.form["lang"], privilege[:-1], now(), request.form["id"]    )
            print q
            query(q)
            
    #read data
    if 'logged_in' in session and session['logged_in']==True:
        #~ flash('New entry was successfully posted')
        q = 'SELECT * FROM pi_user WHERE id=%s' %session['user_id']
        pi_user = query(q)[0]
        q ='SELECT * FROM pi_privilege'
        pi_privilege = query(q)
        return render_template("setup_user.html", pi_user=pi_user, pi_privilege=pi_privilege, error=error )
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
        return render_template("status.html")
    else:
        return render_template("login.html")   




@app.route('/welcome')
def welcome():
    return render_template('welcome.html')
    
@app.route('/hello')
def hello():
    session['ciccio'] = 'user_name'
    print session.get('ciccio')
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
        q = 'SELECT * FROM pi_user WHERE username = "%s" AND password = "%s"' %(request.form["username"],request.form["password"])
        res = query(q)[0]
        if res and len(res) > 0:
            session['logged_in'] = True
            session['user_name'] = res['name']
            session['user_id'] = res['id']
            return render_template("hello.html", error=error)
        else:
            session['logged_in'] = None
            error = "invalid password or username. Please retry"
    return render_template("login.html", error=error)
    

    
if __name__ == '__main__':
    #~ app.secret_key = 'super secret key'
    #~ app.config['SESSION_TYPE'] = 'filesystem'
    #~ app.permanent_session_lifetime  = 5000
    #~ sess.init_app(app)
    app.run(
        host="0.0.0.0", 
        port=int("5000"), 
        debug=True 
    )
    #~ babel = Babel(app)

