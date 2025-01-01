#!/bin/sh

# HARD BLOCKED
echo "Hard blocked!!"
exit

# Clear db
sqlite3 ../db.sqlite3 < clear-db.sql
rm -f  ../studenthome/images/*.jpeg
