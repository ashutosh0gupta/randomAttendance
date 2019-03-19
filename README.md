# Random Attendance
For taking random attendance in the class

# Setting up
  1. __Copy this code to the following folder__

   ```
   ~/randomAttendance
   ```

  (may be, code can run from anywhere! Needs testing.)

  2. __Install dependencies: Django and the others__
  
   ```
   $sudo apt update
   $sudo apt-get install python3 python3-pip mysql-server
   $pip3 install Django
   $pip3 install django-mathfilters
   ```

  -- the above list may not be exhaustive (let us know the missing dependencies)

  3. __Initialize db__

  ```
  $cd ~/randomAttendance
  $python3 manage.py makemigrations studenthome
  $python3 manage.py migrate
  ```
  
  4. __Import student data into the db__

 * Goto IITB ASC webpage with the list of students with pictures and without CPIs
 * Save the page from the browser (tested only on Firefox) to /tmp folder
    (Yes! literally save the page from the browser.)
 * Run ~/randomAttendance/scripts/asc-import.py which generates /tmp/output.csv in the following format

 ```
 1,[rollno1],STUDENT NAME1,[rollno1].jpeg
 2,[rollno2],STUDENT NAME2,[rollno2].jpeg
 ....
 ```
  and /tmp/[rollno*].jpeg for each student .
 
 * Start server of the application

   ```
   $cd ~/randomAttendance
   $python3 manage.py runserver
   ```
    
 * Go to the following webpage in a browser. It will import the students from the csv file.

    http://127.0.0.1:8000/import/

  If the studnet list is long, it will take some 10s of seconds.

  5. __Using attendance__

  - Start server of the application

   ```
   $cd ~/randomAttendance
   $python3 manage.py runserver
   ```

  - For attendance, go to the following webpage in a browser

     http://127.0.0.1:8000/

  - Special pages

     To see the details of a student     
     http://127.0.0.1:8000/[student rollno]

     Find a student who was never called
     http://127.0.0.1:8000/never

     To see the status of all the students
     http://127.0.0.1:8000/all

     To import students
     http://127.0.0.1:8000/import

  - Policy of choosing a random student

  The policy is implemented by function pick_a_student in file ~/randomAttendance/studenthome/views.py


# Other notes for development

(should not be relevant to a user)

- Django help

  https://docs.djangoproject.com/en/2.1/intro/tutorial02/
  
  https://www.youtube.com/watch?v=UmljXZIypDc&index=1&list=PL-osiE80TeTtoQCKZ03TU5fNfx2UY6U4p

- to create a app inside a new project

   $python manage.py startapp



