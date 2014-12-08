#!/usr/bin/python
from flask import *
import sys
import datetime
#~ from flask.ext.babel import gettext, ngettext
#~ from functools import wraps
import sqlite3
#~ import RPi.GPIO as GPIO
import smbus as smbus


app = Flask(__name__)
app.secret_key = 'why would I tell you my secret key?'

    
#~ i2c_addr = 0x20
#~ temp = 0x55AA
#~ i2c = smbus.SMBus(1)
#~ i2c.write_byte(i2c_addr,0x20)



def now():
    return datetime.datetime.now()

DATABASE = '/home/pi/dcn/db/db.sqlite'

def conn_db():
    return sqlite3.connect(DATABASE)

def query_db(query, args=(), one=False):
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


@app.route('/setup_area', methods=["GET","POST"])
def setup_area():    
    q = 'SELECT * FROM pi_area'
    pi_area = query_db(q)
    return render_template("setup_area.html", pi_area=pi_area)

@app.route('/doc')
def doc():    
    return render_template("doc.html")

@app.route('/setup_program')
def setup_program():
    if 'logged_in' in session and session['logged_in']==True:
        return render_template("setup_program.html")
    else:
        return render_template("login.html")   

@app.route('/setup_user', methods=["GET","POST"])
def setup_user():
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
            query_db(q)
            
    #read data
    if 'logged_in' in session and session['logged_in']==True:
        #~ flash('New entry was successfully posted')
        q = 'SELECT * FROM pi_user WHERE id=%s' %session['user_id']
        pi_user = query_db(q)[0]
        q ='SELECT * FROM pi_privilege'
        pi_privilege = query_db(q)
        return render_template("setup_user.html", pi_user=pi_user, pi_privilege=pi_privilege, error=error )
    else:
        return render_template("login.html")




@app.route('/status')
def status():
    if 'logged_in' in session and session['logged_in']==True:
        return render_template("status.html")
    else:
        return render_template("login.html")   

@app.route("/")
@app.route('/home')
def home():
    return render_template("home.html")

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
    error = None
    if request.method == "POST":
        q = 'SELECT * FROM pi_user WHERE username = "%s" AND password = "%s"' %(request.form["username"],request.form["password"])
        res = query_db(q)[0]
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

