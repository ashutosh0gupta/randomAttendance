# randomAttendance
For taking random attendance in the class


# dependencies
  # python package dependencies
  apt-get install pip


# setting up this
  - Needs Django
  - db needs to be initialized
  - data has to be imported

# Some Django help
https://docs.djangoproject.com/en/2.1/intro/tutorial02/
https://www.youtube.com/watch?v=UmljXZIypDc&index=1&list=PL-osiE80TeTtoQCKZ03TU5fNfx2UY6U4p

# to create a app inside the project
python manage.py startapp

# 

# importing students in the DB

- Goto ASC webpage with the list of students with pictures and without CPIs
- Save the page from the browser (tested only on Firefox) to ~/downloads folder
- Run ./scripts/asc-import.csv
- Now go to the following webpage

    http://127.0.0.1:8000/import/