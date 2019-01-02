# after changes in models.py, apps.py generate migration code
python manage.py makemigrations studenthome 
# apply the migration 
python manage.py migrate
