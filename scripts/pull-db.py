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

def pull_files( src, dest ):
    cmd = ['scp', server+':'+src, dest]
    cmd = ' '.join(cmd)
    print(cmd)
    returned_value = os.system(cmd) 

pull_files( '/var/log/nginx/access.log', './tmp/' )

pull_files( '~/randomAttendance/db.sqlite3', './old-dbs/random-'+date+'-db.sqlite3' )
pull_files( '~/randomAttendance/debug.error.log', './tmp/random-debug.error.log' )
pull_files( '~/randomAttendance/debug.log', './tmp/random-debug.log' )

# pull_files( '~/krishnaAttendance/db.sqlite3', './old-dbs/krishna-'+date+'-db.sqlite3' )
# pull_files( '~/krishnaAttendance/debug.error.log', './tmp/krishna-debug.error.log' )
# pull_files( '~/krishnaAttendance/debug.log', './tmp/krishna-debug.log' )

# scp user@cs433.cse.iitb.ac.in:~/randomAttendance/db.sqlite3 cs433-2022-db.sqlite3
