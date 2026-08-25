#!/usr/bin/python3
#

import re
import os
import shutil
import sys
import codecs
from datetime import datetime

# pull db
server="user@cs433.cse.iitb.ac.in"
date=str(datetime.now().date())


returned_value = os.system('mkdir -p ./tmp') 

def remote_run(cmd):
    cmd = ['ssh', server,"'"+cmd+"'"]
    cmd = ' '.join(cmd)
    print(cmd)
    returned_value = os.system(cmd) 

def pull_files( src, dest ):
    cmd = ['scp', server+':'+src, dest]
    cmd = ' '.join(cmd)
    print(cmd)
    returned_value = os.system(cmd) 


#remote_run('cd randomAttendance')

remote_run('cd randomAttendance && source ../Env/randomAttendance/bin/activate &&  python manage.py dumpdata --indent 2 > backup.json')

pull_files( '~/randomAttendance/backup.json', './old-dbs/random-'+date+'-db.json' )
pull_files( '~/randomAttendance/debug.error.log', './tmp/random-debug.error.log' )
pull_files( '~/randomAttendance/debug.log', './tmp/random-debug.log' )
pull_files( '/var/log/nginx/access.log', './tmp/' )

# pull_files( '~/krishnaAttendance/db.sqlite3', './old-dbs/krishna-'+date+'-db.sqlite3' )
# pull_files( '~/krishnaAttendance/debug.error.log', './tmp/krishna-debug.error.log' )
# pull_files( '~/krishnaAttendance/debug.log', './tmp/krishna-debug.log' )

# scp user@cs433.cse.iitb.ac.in:~/randomAttendance/db.sqlite3 cs433-2022-db.sqlite3
