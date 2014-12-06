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


def conn():
    dbname = '/home/pi/dc/db/db.sqlite'
    return sqlite3.connect(dbname)

@app.route("/")
@app.route('/home')
def home():
    return render_template("home.html")
    
@app.route('/hello')
def hello():
    a = conn()
    g.db = conn()
    cur = g.db.execute('SELECT name FROM pi_user WHERE id=1')
    user = cur.fetchall()
    g.db.close()
    return render_template("hello.html", name=user[0][0])
    
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You are logged out')
    return redirect (url_for('login'))

@app.route("/login", methods=["GET","POST"])    
def login():
    error = None
    if request.method == "POST":
        if request.form["username"] != "admin" and request.form["password"] != "admin":
            error = "invalid password or username. Please retry"
        else:
            session['logged_in'] = True
            return redirect(url_for("hello"))
    return render_template("login.html", error=error)
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int("5000"), debug=True )
    app.config.from_pyfile('dc.cfg') #Domocontrol Configure
    babel = Babel(app)

