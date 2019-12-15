import os
import sys
from dotenv import load_dotenv
load_dotenv()
load_dotenv(verbose=True)


EMAIL_BACKEND = 'post_office.EmailBackend'
EMAIL_USE_TLS = True
# SECRET_KEY = os.getenv('SECRET_KEY')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_PORT = 25
DEFAULT_FROM_EMAIL = 'office@cse.iitb.ac.in'


POST_OFFICE = {
    'THREADS_PER_PROCESS' : 10,
    'SENDING_ORDER': ['created'],
    'LOG_LEVEL' : 2,
}

POST_OFFICE_CACHE = False
