#!/usr/bin/python3
#
# after the run check if all the students from the webpage have
# been processes accurately.
#

import re
import os
import shutil

path_to_saved_asc_page = '~/downloads/'
dump_path='/tmp/'

path_dir = os.path.expanduser( path_to_saved_asc_page )
dump_dir = os.path.expanduser( dump_path )
    
jpeg_dir= path_dir + '/Welcome to ASC !_files/CourseList_data'
in_file = path_dir + '/Welcome to ASC !_files/CourseList.html'
out_file = os.path.expanduser(dump_dir+'output.csv')
output = open(out_file,'w+')
input = open(in_file).read()

flat_tds = re.sub(r'td>[\s]*<td', r'td><td', input, flags=re.M)

p = re.compile(r'(\d?\d?\d)\.\*?</b></td><td align="center"><b> ([0-9A-Z]+)</b></td><td> ([a-zA-Z \.]*)</td><td align="center"> Credit </td><td><img src="CourseList_data/([a-zA-Z0-9_]+.jpeg)')
out = p.findall(flat_tds)
os.chdir(jpeg_dir)
for o in out:
    shutil.copy(o[3],dump_dir+o[1]+".jpeg")
    output.write("%s,%s,%s,%s\n" % (o[0],o[1],o[2],o[1]+".jpeg"))
    
print (len(out))
output.close()
