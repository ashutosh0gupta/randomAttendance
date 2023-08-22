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

pull_files( '/var/log/nginx/access.log.2.gz', './tmp/' )
# pull_files( '/var/log/nginx/access.log.1', './tmp/' )
# pull_files( '/var/log/nginx/access.log', './tmp/' )


# scp user@cs433.cse.iitb.ac.in:~/randomAttendance/db.sqlite3 cs433-2022-db.sqlite3
