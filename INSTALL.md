=== INSTALLATION ===
sudo apt-get install python-smbus
sudo apt-get install i2c-tools

To show address of I2C type: (see /etc/i2c-x)
sudo i2cdetect -y 1     #1 or 0, see /dev(i2c-x)

sudo pip install Flask  #webserver
sudo easy_install virtualenv  #to install flask
sudo pip install Flask-Babel #to install translation plugin


chmod +x dc.py

== RUN ===
./dc.py


Per segnalare errori, modifiche, soluzioni, consigli -> https://github.com/lucasub/domocontrol/issues/new

Grazie
------
