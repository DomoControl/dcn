#!/bin/bash 
#Use this commend to make translation
/usr/local/bin/pybabel extract -F babel.cfg -o messages.pot .
/usr/local/bin/pybabel update -i messages.pot -d translations
/usr/local/bin/pybabel compile -d translations
