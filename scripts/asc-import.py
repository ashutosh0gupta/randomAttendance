#!/usr/bin/python3
#
# after the run check if all the students from the webpage have
# been processes accurately.
#

import re
import os
import shutil
import sys

path_to_saved_asc_page = '/tmp/'
dump_path='/tmp/'

path_dir = os.path.expanduser( path_to_saved_asc_page )
dump_dir = os.path.expanduser( dump_path )
    
jpeg_dir= path_dir + '/Welcome to ASC !_files/'
in_file = path_dir + '/Welcome to ASC !_files/Login.html'
# jpeg_dir= path_dir + '/Welcome to ASC !_files/CourseList_data'
# in_file = path_dir + '/Welcome to ASC !_files/CourseList.html'

out_file = os.path.expanduser(dump_dir+'output.csv')
output = open(out_file,'w+')

try:
    with open(in_file) as in_f:
        input = in_f.read()
except IOError as e:
    print( "failed to open" + in_file + "\nHave you downloaded ASC webpage at " + path_to_saved_asc_page + "?" )
    sys.exit(0)

flat_tds = re.sub(r'td>[\s]*<td', r'td><td', input, flags=re.M)
flat_tds = re.sub(r'>[\s]*<a', r'><a', flat_tds, flags=re.M)
flat_tds = re.sub(r'>[\s]*<b>', r'><b>', flat_tds, flags=re.M)
flat_tds = re.sub(r'b>[\s]*</a>[\s]*</td', r'b></a></td', flat_tds, flags=re.M)

# print(flat_tds)

#2018 asc pattern
#p = re.compile(r'(\d?\d?\d)\.\*?</b></td><td align="center"><b> ([0-9A-Z]+)</b></td><td> ([a-zA-Z \.]*)</td><td align="center"> Credit </td><td><img src="CourseList_data/([a-zA-Z0-9_]+.jpeg)')

# 2020 ASC pattern
# p = re.compile(r'(\d?\d?\d)\.\*?</b></td><td align="center"><a href="[^<>"]*"><b> ([0-9A-Z]+)</b></a></td><td> ([a-zA-Z \.]*)</td>(<td>[^><"]*</td>){4}<td align="center">[^><"]*</td><td>[^><"]*</td><td><img src="CourseList_data/([a-zA-Z0-9_]+.jpeg)')

# 2021 ASC pattern
# p = re.compile(r'(\d?\d?\d)\.\*?</b></td><td align="center"><a href="[^<>"]*"><b> ([0-9A-Z]+)</b></a></td><td> ([a-zA-Z \.]*)</td>(<td>[^><"]*</td>){5}<td align="center">[^><"]*</td><td>[^><"]*</td><td><img src="CourseList_data/([a-zA-Z0-9_]+.jpeg)')

# 2022 ASC pattern: otimized pattern; hostel info added 
# p = re.compile(r'(\d?\d?\d)</td>.*<td align="center"><a href=[^<>]*><b> ([0-9A-Z]+)</b></a></td><td> ([a-zA-Z \.]*)</td>(<td[^<]*</td>){7}<td><img.*CourseList_data/([a-zA-Z0-9_]+.jpeg)')

# 2022 ASC pattern: otimized pattern; hostel info added 
# p = re.compile(r'(\d?\d?\d)</td>.*<td align="center"><a href=[^<>]*><b> ([0-9A-Z]+)</b></a></td><td> ([a-zA-Z \.]*)</td>(<td[^<]*</td>){8}<td><img.*CourseList_data/([a-zA-Z0-9_]+.jpeg)')

# 2023 ASC pattern: downloaded via chrome 
p = re.compile(r'(\d?\d?\d)</td>.*<td align="center"><a href=[^<>]*><b> ([0-9A-Z]+)</b></a></td><td> ([a-zA-Z \.]*)</td>(<td[^<]*</td>){8}<td><img.*src="([^>]*)">')



out = re.findall( p, flat_tds)

# print(out)
# exit()
# print(len(out))
# for o in out:
#     print(o)
#     exit()


os.chdir(jpeg_dir)
for o in out:
    # print(o)
    index  = o[0]
    rollno = o[1]
    name   = o[2]
    photo  = o[4]     # o[3] is junk    
    if os.path.isfile( photo ):
        student_image_file = rollno+".jpeg"
        shutil.copy(photo, dump_dir+student_image_file)
        print ( "File created : "+ dump_dir+student_image_file)
    else:
        print ( "Missing photo : "+ rollno )
        student_image_file = "none"       
    output.write("%s,%s,%s,%s\n" % (index,rollno,name,student_image_file))

print ( "File created : "+ out_file)  
print ( "Students processed : "+ str(len(out)))
print ( "Inspect " + out_file + " to check integrity of the processing!")

output.close()
