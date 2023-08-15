#!/usr/bin/python3
#

import re
import os
import shutil
import sys
import codecs
from datetime import datetime

path_dir = os.path.expanduser( './' )    
in_file = path_dir + 'debug.log'

try:
    with open(in_file, encoding='ISO-8859-1') as in_f:
        input = in_f.read()
except IOError as e:
    print( "failed to open" + in_file )
    sys.exit(0)


p = re.compile(r'ERROR ([0-9A-Z\-]+) ([0-9:,]+) views ([0-9A-Z]+) submitting, while quiz is closed')
missed = re.findall( p, input)
p = re.compile(r'INFO ([0-9A-Z\-]+) ([0-9:,]+) views ([0-9A-Z]+) answered-([0-9]+)')
answered = re.findall( p, input)

start_date = datetime.strptime('2023-07-01', '%Y-%m-%d')
miss_map = {}

quiz_class_map = { 93 :'Lecture2',  # Lecture2
                   96 :'Lab1    ',  # Lab1
                   101:'Lecture4',  # Lecture4
                   98 :'Lecture5',  # Lecture5
                   99 :'Lecture6',  # Lecture6
                   100:'Lab2    ',  # Lab2
                   102:'Lecture7',  # Lecture7
                  }

quiz_num_map = {'2023-08-03':93,   
                '2023-08-04':96,   
                '2023-08-05':0,    # ?? << Nothing was done on the day
                '2023-08-07':101,  
                '2023-08-08':98,   
                '2023-08-10':99,   
                '2023-08-11':100,  
                '2023-08-14':102,
                }

for o in missed:
    # print(o)
    date   = o[0]
    time   = o[1]
    rollno = o[2]
    # date = datetime.strptime(date+' '+time[:-4], '%Y-%m-%d %H:%M:%S')
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    if date_obj > start_date:
        qid = quiz_num_map[date]
        if qid == 0:
            continue
        if not qid in miss_map:
            miss_map[qid] = set()
        miss_map[qid].add(rollno)
        # if not rollno in miss_map:
        #     miss_map[rollno] = set()
        # miss_map[rollno].add(date)

for o in answered:
    date   = o[0]
    time   = o[1]
    rollno = o[2]
    quiz   = int(o[3])
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    if date_obj > start_date:
        if rollno in miss_map[quiz]:
            miss_map[quiz].remove(rollno)

print('Late sumbmissions:')
for d in miss_map:
    print(quiz_class_map[d], end=" ")
    for r in miss_map[d]:
        print( r, end=" ")
    print()

# print(miss_map)
# print(len(out))
# for o in out:
#     print(o)
# exit()


# os.chdir(jpeg_dir)
# for o in out:
#     # print(o)
#     index  = o[0]
#     rollno = o[1]
#     name   = o[2]
#     photo  = o[4]     # o[3] is junk    
#     if os.path.isfile( photo ):
#         student_image_file = rollno+".jpeg"
#         shutil.copy(photo, dump_dir+student_image_file)
#         print ( "File created : "+ dump_dir+student_image_file)
#     else:
#         print ( "Missing photo : "+ rollno )
#         student_image_file = "none"       
#     output.write("%s,%s,%s,%s\n" % (index,rollno,name,student_image_file))

# print ( "File created : "+ out_file)  
# print ( "Students processed : "+ str(len(out)))
# print ( "Inspect " + out_file + " to check integrity of the processing!")

# output.close()
