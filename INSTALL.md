# INSTALLATION INSTRUCTIONS

The following instructions describe how to install the CIM Questionnaire on a Unix-type server (Cent-OS, Linux, Mac-OSX) for the purpose of starting to use and test the web application. 

## PRE-REQUISITES

The system must have the following Python packages installed:

* Python 2.7.2+
* Django 1.6+
* South
* libXML
* pytz
* PIL
* django-registration, django-authopenid (build from source)
* A PostGres database is recommended.  However, Django also supports MySQL and SQLite3.
    * To use PostGres you must install psycopg2.

## DOWNLOAD

Download the software at the desired version from the github repository

```sh
cd <install directory>
tar xvfz django-cim-forms.<version>.tar.gz
cd CIM_Questionnaire
```

## CONFIGURATION

* Generate a configuration file. The preferred location is ``$HOME/.config/esdoc-questionnaire.conf``. A custom location may be used in which case the ``settings.py`` variable ``CONF_PATH`` should be modified to match the location of the file. A template is available in the repository's top-level director called ``esdoc-questionnaire.conf.TEMPLATE`` The format of the configuration file is:

```ini
[database]
engine=django.db.backends.postgresql_psycopg2
name=questionnaire
user=
password=
host=127.0.0.1
port=5432

[settings]
secret_key=
static_root=static/
```

* review settings.py

  verify that the db/port/user/pwd exist (postgres is recommended; try `createdb <db> -O <user> -p <port>`)
  to avoid profiling (recommended) set PROFILE and SETUP_HPY to "False"
  if needed, update STATIC_ROOT and STATICFILES_DIR
  if desired, set EMAIL_HOST and EMAIL_HOST_USER and EMAIL_HOST_PASSWORD and DEFAULT_FROM_EMAIL and SERVER_EMAIL

  for production deployments, it is recommended to set DEBUG to "False" and add the appropriate value(s) for ALLOWED_HOSTS

* start a virtual python environment (recommended)

```sh
pip install django
pip install psycopg2 (may require `sudo get-apt install libq-dev`)
pip install lxml (may require `sudo get-apt install libxml2` and/or `sudo get-apt install libxslt`)
pip install django-openid-auth python-openid
pip install django_mptt
pip install pytz
pip install south
pip install guppy (for profiling)
```

## INITIALIZATION

* python manage.py syncdb 

  this may generate a "transaction aborted" DatabaseError; this is an issue w/ v0.9.9.6 which will be fixed in future versions; for now comment out the offending bits of django_cim_forms/cim_1_5/forms.py, dycore/forms.py, dycore/models.py, dcf/cim_1_8_1/models/generated_models.py; then un-comment them once `syncdb` succeeds
  
  this may generate a "value too long" DatabaseError; this is a known issue w/ Django and PostGres; to fix it run `python manage.py dbshell < django_postgres_fix_sql`

* python manage.py migrate dcf 
* gather the static media files from the different applications into a single directory; first ensure location specified in settings.py by STATIC_ROOT exists

```sh
python manage.py collectstatic
```

* copy over initial data

```sh
python manage.py loaddata fixtures/*.gz
```

## STARTUP

* Start the CIM Questionnaire either via the embedded Django server:

```sh
python manage.py runserver
```

  or through apache:

  ensure apache conf is properly setup and restart the apache server

## USE

* ordinarily admins would have to manually upload and register Controlled Vocabularies and Categorizations (and Projects and Versions); using fixtures, as above, avoids this requirement
* the ATOM feed functionality requires that the correct domain be specifed in the "sites" table via the admin interface.
