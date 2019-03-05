# after changes in models.py, apps.py generate migration code
python3 manage.py makemigrations studenthome 
# apply the migration 
python3 manage.py migrate
