#!/usr/bin/python3
#

import re
import os
import shutil
import sys
import codecs
from datetime import datetime

os.system('source ../Env/randomAttendance/bin/activate')
os.system('curl --location-trusted -u akg:.... "https://internet-sso.iitb.ac.in/login.php"')
os.system('git pull')
os.system('python3 ./manage.py makemigrations')
os.system('python3 ./manage.py migrate')
os.system('sudo systemctl daemon-reload && sudo systemctl restart gunicorn')
