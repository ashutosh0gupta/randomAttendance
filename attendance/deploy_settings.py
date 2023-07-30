import os
from .settings import BASE_DIR

MOUNT_SUB_URL="course_vm/cs433/"

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True


#SECURE_HSTS_SECONDS = 60
#SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True


#STATIC_URL = '/'+MOUNT_SUB_URL+'static/'
STATIC_URL = '/course_vm/cs433/static/'
STATIC_ROOT = os.path.join(BASE_DIR,'static')
#STATICFILES_DIRS = [(os.path.join(BASE_DIR, 'static')),]



#MEDIA_URL = '/'+MOUNT_SUB_URL+'images/'
MEDIA_URL = '/course_vm/cs433/images/'
MEDIA_ROOT = 'studenthome/images'


