#!/usr/bin/python3

import re
import os

out_file = os.path.expanduser('~/downloads/output.csv')
in_file = os.path.expanduser('~/downloads/CourseList.html')
output = open(out_file,'w+')
input = open(in_file).read()

flat_tds = re.sub(r'td>[\s]*<td', r'td><td', input, flags=re.M)

p = re.compile(r'(\d?\d)\.\*?</b></td><td align="center"><b> ([0-9A-Z]+)</b></td><td> ([a-zA-Z ]*)</td><td align="center"> Credit </td><td><img src="CourseList_data/([a-zA-Z0-9_]+.jpeg)')
out = p.findall(flat_tds)
for o in out:
    output.write("%s,%s,%s,%s\n" % (o[0],o[1],o[2],o[3]))
    
# print(out)
print (len(out))
output.close()
