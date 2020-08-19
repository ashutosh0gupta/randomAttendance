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
  Write the following content in randomAttendance/attendance/.env
  ```
  SECRET_KEY="<django-secret-key>"
  AUTH_LDAP_SERVER_URI="<your-ldap-server>"
  EMAIL_HOST="smtp.<your-smtp-server>"
  EMAIL_HOST_USER="<user-on-smtp-server>"
  EMAIL_HOST_PASSWORD="<password-of-the-user>"
  ```

* Use the following shell command to generate a random django-secret-key key

   $tr -dc 'a-z0-9!@#$%^&*(-_=+)' < /dev/urandom | head -c50

4. __Import student data into the db__

 * Goto IITB ASC webpage with the list of students with default options
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


# Setting up nginix gunicorn

 - nginix config file located at /etc/ngnix/sites-enabled/

```
server{
        listen 443 ssl http2;
        listen [::]:443 ssl http2;
        server_name <SERVERNAME(S)>;
        #server_name _;
        # the following file should contain the location of certificate
        include snippets/signed.conf;
        # the following file should contain the parameter of ssl
        include snippets/ssl-params.conf;
        client_max_body_size 100M;
        location = /favicon.ico {access_log off; log_not_found off; }

	location <MOUNT POINT>/static/{
                alias <ABSOLUTE PATH TO APP>/randomAttendance/static/;
        }
        location <MOUNT POINT>/images/{
                alias <ABSOLUTE PATH TO APP>/randomAttendance/studenthome/images/;
        }

        # do we need these? Can we remove these
	location / {
                include proxy_params;
                proxy_read_timeout 300s;
                proxy_connect_timeout 75s;
                proxy_pass http://unix:<ABSOLUTE PATH TO APP>/randomAttendance/attendance.sock;
        }

	location <MOUNT POINT>/ {
                include proxy_params;
                proxy_read_timeout 300s;
                proxy_connect_timeout 75s;
                proxy_pass http://unix:<ABSOLUTE PATH TO APP>/randomAttendance/attendance.sock;
        }

}
```


 - gcunicorn config file located at /etc/systemd/system/attendance.service

TODO: find instructions for creating environment. Can we move Env inside the app folder?

```
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=user
Group=www-data
WorkingDirectory=<ABSOLUTE PATH TO APP>/randomAttendance
Environment="PATH=<ABSOLUTE PATH TO APP>/Env/randomAttendance/bin"
ExecStart=<ABSOLUTE PATH TO APP>/Env/randomAttendance/bin/gunicorn --access-logfile - --workers 3 --bind unix:<ABSOLUTE PATH TO APP>/randomAttendance/attendance.sock attendance.wsgi:application


[Install]
WantedBy=multi-user.target
```

# Instruction for updating djano project on server

'''
$ cd randomattendance/
$ source source ../Env/randomAttendance/bin/activate

$ git pull
> or any changes to project $ python manage.py createsuper

$ sudo systemctl daemon-reload && sudo systemctl restart gunicorn
>(reloads project and restart gcunicorn service;repeat this after any change)

$ sudo systemctl status gunicorn
> (check if there is any error or not, should say guicorn service is active)

$ sudo nginx -t && sudo systemctl restart nginx
> (checks nginx config file and restarts the nginx server)

$ deactivate
'''

One command to restart and nginx together.[Risky may cause error]

'''
$ sudo systemctl daemon-reload && sudo systemctl restart gunicorn && sudo systemctl restart nginx
'''

# Other notes for development

(should not be relevant to a user)

- Django help

  https://docs.djangoproject.com/en/2.1/intro/tutorial02/
  
  https://www.youtube.com/watch?v=UmljXZIypDc&index=1&list=PL-osiE80TeTtoQCKZ03TU5fNfx2UY6U4p

- to create a app inside a new project

   $python manage.py startapp



