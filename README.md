# randomAttendance
For taking random attendance in the class

# setting up
  1. Install dependencies: Django and the others
  
   ```
   $sudo apt update
   $apt-get install python3 python3-pip
   $pip3 install Django
   $pip3 install django-mathfilters
   ```

  -- the above list may not be exaustive (let us know the missing dependencies)

  2. db needs to be initialized

  ```
  $python3 manage.py migrate
  ```
  
  3. import student data

 * Goto ASC webpage with the list of students with pictures and without CPIs
 * Save the page from the browser (tested only on Firefox) to ~/downloads folder
 * Run ./scripts/asc-import.csv which generates /tmp/output.csv and /tmp/<rollno>.jpeg files
 * Start server of the application

   ```
   $python3 manage.py runserver
   ```
    
 * Now go to the following webpage in a browser

    http://127.0.0.1:8000/import/

  4. Using attendance

  - Start server of the application

   ```
   $python3 manage.py runserver
   ```

  - For attendance, go to the following webpage in a browser

     http://127.0.0.1:8000/

  - Special pages

     To see the details of a student     
     http://127.0.0.1:8000/<student rollno>

     Find a student who was never called
     http://127.0.0.1:8000/never

     To see the status of all the students
     http://127.0.0.1:8000/all

     To import students
     http://127.0.0.1:8000/import


# other notes for devlopment (should not be relavant to a user)

- Django help

  https://docs.djangoproject.com/en/2.1/intro/tutorial02/
  
  https://www.youtube.com/watch?v=UmljXZIypDc&index=1&list=PL-osiE80TeTtoQCKZ03TU5fNfx2UY6U4p

- to create a app inside a new project

   $python manage.py startapp


