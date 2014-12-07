#!/usr/bin/python
from flask import *
from flask.ext.babel import gettext, ngettext
from functools import wraps
import sqlite3
#~ import RPi.GPIO as GPIO
import smbus as smbus


    
    
i2c_addr = 0x20
temp = 0x55AA
i2c = smbus.SMBus(1)
i2c.write_byte(i2c_addr,0x20)

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = 'secret'
dbname = '/home/pi/dc/db/db.sqlite'
DATABASE = '/home/pi/dc/db/db.sqlite'
    
def conn_db():
    return sqlite3.connect(dbname)

def query_db(query, args=(), one=True):
    cur = conn_db().execute(query, args)
    rv = [dict((cur.description[idx][0], value)
        for idx, value in enumerate(row)) for row in cur.fetchall()]
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.route("/")
@app.route('/home')
def home():
    return render_template("home.html")
    
@app.route('/hello')
def hello():
    return render_template("hello.html", name=session['user_name'])
    
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You are logged out')
    return redirect (url_for('login'))

@app.route("/login", methods=["GET","POST"])    
def login():
    error = None
    if request.method == "POST":
        res = query_db('SELECT * FROM pi_user WHERE username = "%s" AND password = "%s"' %(request.form["username"],request.form["password"]))
        if res and len(res) > 0:
            session['logged_in'] = True
            session['user_id'] = res['id']
            session['user_name'] = res['name']
            return redirect(url_for("hello"))
        else:
            error = "invalid password or username. Please retry"
    return render_template("login.html", error=error)
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int("5000"), debug=True )
    app.config.from_pyfile('dc.cfg') #Domocontrol Configure
    babel = Babel(app)

