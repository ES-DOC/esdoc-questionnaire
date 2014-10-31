# Django settings for CIM_Questionnaire project.
from ConfigParser import SafeConfigParser
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
import os


rel = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

# Path to the configuration file containing secret values.
# TODO: EITHER MOVE THE LOCATOIN OF THE CONF FILE OR MAKE ITS NAME UNIQUE (TO HANDLE CONCURRENT DEPLOYMENTS)
CONF_PATH = os.path.join(os.path.expanduser('~'), '.config', 'esdoc-questionnaire.conf')

parser = SafeConfigParser()
parser.read(CONF_PATH)

DEBUG = parser.getboolean('debug','debug')
DEBUG_TOOLBAR = parser.getboolean('debug','debug_toolbar') # this enables django-debug-toolbar (look in project-level "urls.py" for more info)
DEBUG_PROFILING = parser.getboolean('debug','debug_profiling')

ADMINS = (
#    ( parser.get('admin', 'name'), parser.get('admin', 'email'))
)

MANAGERS = ADMINS


EMAIL_HOST = parser.get('email', 'host')
EMAIL_PORT = parser.get('email', 'port')
EMAIL_HOST_USER = parser.get('email', 'username')
EMAIL_HOST_PASSWORD = parser.get('email', 'password')
EMAIL_USE_TLS = True

# DB SETTINGS
DATABASES = {
    'default': {
        'ENGINE'    : parser.get('database', 'engine'), # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME'      : parser.get('database', 'name'),                      # Or path to database file if using sqlite3.
        'USER'      : parser.get('database', 'user'),
        'PASSWORD'  : parser.get('database', 'password', raw=True),
        'HOST'      : parser.get('database', 'host'),                              # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT'      : parser.get('database', 'port'),                                   # Set to empty string for default.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Denver'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# this is overwritten in questionnaire.__init__.py
SITE_NAME = parser.get('site','name')
SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = rel('site_media/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/site_media/'


# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = rel(parser.get('settings', 'static_root', raw=True))

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = parser.get('settings', 'secret_key', raw=True)

# List of callables that know how to import templates from various sources.
# (note templates are cached in production mode)
if not DEBUG:
    TEMPLATE_LOADERS = (
        ('django.template.loaders.cached.Loader', (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        )),
    )
else:
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # openid requirement
    #'django_authopenid.middleware.OpenIDMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    #'django_openid_auth.auth.OpenIDBackend',
)


ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    rel('templates/'),
    rel(parser.get('settings', 'static_root', raw=True)),
)

# makes 'request' object available in templates
TEMPLATE_CONTEXT_PROCESSORS += (
     'django.core.context_processors.request',
     # requirement of messaging framework...
     'django.contrib.messages.context_processors.messages',
     # requirement of openid
     #'django_authopenid.context_processors.authopenid',
)

# login page
LOGIN_URL = '/login'
# page to redirect after successfull authentication, if 'next' parameter is not provided
LOGIN_REDIRECT_URL='/' 

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',    
    'django.contrib.admindocs',
    # testing / debugging / profiling apps are added conditionally below
    # db migration...
    'south',
#    # openid authentication...
#    #'django_openid_auth',
#    #'django_authopenid',
    # time-zone aware stuff...
    'pytz',
    # efficient hierarchies of models...
    'mptt',
    # main project app...
    'questionnaire',
    # viewing remote mindmaps...
    'mindmaps',
    # old apps from DCMIP-2012...
    'django_cim_forms', 'django_cim_forms.cim_1_5', 'dycore',
    # old apps from QED...
#    'dcf', 'dcf.cim_1_8_1',
)

OPTIONAL_INSTALLED_APPS = [
    # list of apps that are installed conditionally
    {
        "condition"  : DEBUG_TOOLBAR,
        "import"     : "debug_toolbar",
        "app"        : ("debug_toolbar", "template_timings_panel", ),   # TODO: CHANGE THIS TO "debug_toolbar.apps.DebugToolbarConfig' IF UPGRADING TO DJANGO 1.7
        "middleware" : ("debug_toolbar.middleware.DebugToolbarMiddleware",),
    },
]

for optional_app in OPTIONAL_INSTALLED_APPS:
   if optional_app.get("condition",False):
#       try:
#           __import__(optional_app["import"])
#       except ImportError:
#           pass
#       else:
       INSTALLED_APPS += optional_app.get("app",())
       # django is pretty ridiculous
       # the order of entries in middleware is very important
       # so rather than append this middleware, insert it as the next-to-last one
       #MIDDLEWARE_CLASSES += optional_app.get("middleware", ())
       MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES[0:-1] + optional_app.get("middleware",()) + (MIDDLEWARE_CLASSES[-1],)


SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# TODO: THIS IS STORING SESSION VARIABLES VIA COOKIES
# OTHER OPTIONS ARE FILE, DB (DEFAULT), OR CACHE
# EVENTUALLY, I SHOULD MOVE TO CACHE: https://docs.djangoproject.com/en/dev/topics/cache/
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_HTTPONLY = True

################################################
# fixing known django / south / postgres issue #
################################################

# before proceeding after the syncdb call
# increase the size of the "name" field in auth_permission if needed

try:

    from django.db.models.signals import post_syncdb
    from django.db import connection

    from django.contrib.auth.models import Permission

    def update_db(sender, **kwargs):

        # when the 1st APP tries to sync,
        # check if auth_permission_name is too small;
        # if so, increase the column size
        if kwargs['app'].__name__ == INSTALLED_APPS[0] + ".models":
            auth_permission_name = Permission._meta.get_field_by_name("name")[0]
            if auth_permission_name.max_length < 100:

                cursor = connection.cursor()

                cursor.execute("ALTER TABLE auth_permission DROP COLUMN name;")
                cursor.execute("ALTER TABLE auth_permission ADD COLUMN name character varying(100);")

    post_syncdb.connect(update_db)

except ImportError:
    # sometimes this module gets loaded outside of the full django framework
    # (as w/ the db scripts)
    pass


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


#########################
# debugging & profiling #
#########################


if DEBUG_TOOLBAR:

    # this is only needed if running via apache
    # BEGIN
    #
    #DEBUG_TOOLBAR_PATCH_SETTINGS = False
    #
    # def show_toolbar(request):
    #     # overloaded from 'debug_toolbar.middleware.show_toolbar'
    #     #if request.META.get('REMOTE_ADDR', None) not in settings.INTERNAL_IPS:
    #     #    return False
    #     #
    #     # if request.is_ajax():
    #     #     return False
    #     #
    #     # return bool(DEBUG_TOOLBAR)
    #
    #     if bool(DEBUG_TOOLBAR):
    #         return not request.is_ajax()
    #
    #     return False
    #
    # DEBUG_TOOLBAR_CONFIG = {
    #     "SHOW_TOOLBAR_CALLBACK" : 'CIM_Questionnaire.settings.show_toolbar',
    # }
    #
    # END

    DEBUG_TOOLBAR_PANELS = [
        #'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        #'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        "template_timings_panel.panels.TemplateTimings.TemplateTimings",    # this is a 3rd party panel
        #'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        #'debug_toolbar.panels.redirects.RedirectsPanel',
    ]

######################################
# tools for usage & memory profiling #
######################################

PROFILE 	 = False
PROFILE_LOG_BASE = rel('profiles/')
SETUP_HPY 	 = False

##################################
# DJANGO_CIM_FORMS ATOM_FEED_DIR #
##################################

ATOM_FEED_DIR = rel('django_cim_forms/feed')

