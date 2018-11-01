"""
WSGI config for pageaudit project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""
import os, sys
import django
from django.core.handlers.wsgi import WSGIHandler

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pageaudit.settings")

env_variables_to_pass = ['DJANGO_ENV',
                         'DJANGO_DEBUG_FLAG',
                         'DJANGO_DB_NAME',
                         'DJANGO_DB_USER',
                         'DJANGO_DB_PASSWORD',
                         'DJANGO_DB_HOST',
                         'DJANGO_STATIC_ROOT',
                         'DJANGO_STATIC_URL',
                         'DJANGO_FORCE_SCRIPT_NAME',
                         # 'DJANGO_LOGIN_URL',
                         'DJANGO_LOGOUT_URL',]

class WSGIEnvironment(WSGIHandler):
    def __call__(self, environ, start_response):
        for var in env_variables_to_pass:
            os.environ[var] = environ.get(var, '')
        return super(WSGIEnvironment, self).__call__(environ, start_response)

django.setup(set_prefix=False)
application = WSGIEnvironment()
