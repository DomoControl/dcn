#!/usr/bin/python
from flask import *
from flask.ext.session import Session
import sys
#~ from flask.ext.babel import gettext, ngettext
#~ from functools import wraps
import sqlite3
#~ import RPi.GPIO as GPIO
import smbus as smbus



    
#~ i2c_addr = 0x20
#~ temp = 0x55AA
#~ i2c = smbus.SMBus(1)
#~ i2c.write_byte(i2c_addr,0x20)

SESSION_TYPE = 'memcache'

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = 'why would I tell you my secret key?'
sess = Session()
DATABASE = '/home/pi/dc/db/db.sqlite'
    
def conn_db():
    return sqlite3.connect(DATABASE)

def query_db(query, args=(), one=False):
    cur = conn_db().execute(query, args)
    rv = [dict((cur.description[idx][0], value)
        for idx, value in enumerate(row)) for row in cur.fetchall()]
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/doc')
def doc():    
    return render_template("doc.html")

@app.route('/setup_user')
def setup_user():
    if 'logged_in' in session and session['logged_in']==True:
        #~ flash('New entry was successfully posted')
        q = 'SELECT * FROM pi_user WHERE id=%s' %session['user_id']
        pi_user = query_db(q)
        q ='SELECT * FROM pi_privilege'
        pi_privilege = query_db(q)
        return render_template("setup_user.html", pi_user=pi_user, pi_privilege=pi_privilege)
    else:
        return render_template("login.html")
    
    
@app.route('/setup_program')
def setup_program():    
    if 'logged_in' in session and session['logged_in']==True:
        return render_template("setup_program.html")
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
        res = query_db(q)
        if res and len(res) > 0:
            session['logged_in'] = True
            session['user_id'] = res['id']
            session['user_name'] = res['name']
            return render_template("hello.html", error=error)
        else:
            session['logged_in'] = None
            error = "invalid password or username. Please retry"
    return render_template("login.html", error=error)
    
if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.permanent_session_lifetime  = 5000
    sess.init_app(app)
    app.run(host="0.0.0.0", port=int("5000"), debug=True )
    #~ babel = Babel(app)

