import os
from decouple import config

class Config(object):
    basedir = os.path.abspath(os.path.dirname(__file__))

    DEBUG = config('DEBUG', default=False, cast=bool)
    if not DEBUG:
        SESSION_COOKIE_HTTPONLY = True
        REMEMBER_COOKIE_HTTPONLY = True
        REMEMBER_COOKIE_DURATION = 3600

    SECRET_KEY = config('SECRET_KEY', default='S#perS3crEt_007')

    DATABASE_URI = config('DATABASE_URI', default='postgresql://localhost/switcherbot')
    
    AUTH0_CLIENT_ID=config('AUTH0_CLIENT_ID')
    AUTH0_CLIENT_SECRET=config('AUTH0_CLIENT_SECRET')
