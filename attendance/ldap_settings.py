import os
import ldap
from django_auth_ldap.config import *
from dotenv import load_dotenv
load_dotenv()
load_dotenv(verbose=True)
# from .populate import populate
# populate()

AUTH_LDAP_SERVER_URI = os.getenv('AUTH_LDAP_SERVER_URI')
AUTH_LDAP_BIND_DN = ''
AUTH_LDAP_BIND_PASSWORD = ''
AUTH_LDAP_USER_SEARCH = LDAPSearch('ou=People,dc=cse,dc=iitb,dc=ac,dc=in',
ldap.SCOPE_SUBTREE, '(uid=%(user)s)')


AUTH_LDAP_USER_ATTR_MAP = {
    'first_name': 'cn',
    'last_name': 'sn',
    'email': 'mail',
}

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    'ou=Groups,dc=cse,dc=iitb,dc=ac,dc=in',
    ldap.SCOPE_SUBTREE,
    '(objectClass=*)',
)

AUTH_LDAP_GROUP_TYPE = PosixGroupType(name_attr='cn')


AUTH_LDAP_MIRROR_GROUPS =  True
AUTH_LDAP_FIND_GROUP_PERMS = True
AUTH_LDAP_CACHE_GROUPS = True

AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_staff" : "cn=webteam,ou=Groups,dc=cse,dc=iitb,dc=ac,dc=in",
    "is_superuser" : "cn=webteam,ou=Groups,dc=cse,dc=iitb,dc=ac,dc=in"
}

AUTH_LDAP_ALWAYS_UPDATE_USER = True

AUTHENTICATION_BACKENDS = [
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
]



