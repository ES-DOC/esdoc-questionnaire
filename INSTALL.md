# INSTALLATION INSTRUCTIONS

The following instructions describe how to install the CIM Questionnaire on a Unix-type server (Cent-OS, Linux, Mac-OSX) for the purpose of starting to use and test the web application. 

## PRE-REQUISITES

The system must have the following Python packages installed:

* Python 2.7.2+
* Django 1.6.5 (pip install django==1.6.5)
* python-memcached (pip install python-memcached)
* mptt (pip install django-mptt)
* pytz (pip install pytz)
* South (pip install south)
* libXML (pip install lxml; may require libxml2-dev and/or libxslt1-dev)
* A PostGres database is recommended.  However, Django also supports MySQL and SQLite3.
    * To use PostGres you must install psycopg2.
* to run w/ profiling install pyinstrument

## DOWNLOAD

Download the software at the desired version from the github repository

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

[cache]
host=127.0.0.1
port=11211

[email]
host=smtp.gmail.com
port=
username=
password=

[settings]
secret_key=
static_root=static/

[debug]
debug=true
debug_toolbar=false
debug_profiling=false
```

* a Django secret key can be generated at: http://www.miniwebtool.com/django-secret-key-generator/

* start a virtual python environment (recommended)

```sh
pip install django
pip install psycopg2 (may require `sudo get-apt install libq-dev`)
pip install lxml (may require `sudo get-apt install libxml2` and/or `sudo get-apt install libxslt`)
pip install django-openid-auth python-openid
pip install django_mptt
pip install pytz
pip install south
pip install python-memcached (may require `sudo get-apt install memcacehd`)
```

## INITIALIZATION

```sh
python CIM_Questionnaire/manage.py syncdb 
python CIM_Questionnaire/manage.py migrate mindmaps
python CIM_Questionnaire/manage.py migrate questionnaire
python CIM_Questionnaire/manage.py collectstatic
```

## STARTUP

* Start the CIM Questionnaire either via the embedded Django server:

```sh
python CIM_Questionnaire/manage.py runserver
```

  or through apache:

  ensure apache conf is properly setup and restart the apache server

## USE

* ordinarily admins would have to manually upload and register Controlled Vocabularies and Categorizations (and Projects and Versions); using fixtures, as above, avoids this requirement
* the ATOM feed functionality requires that the correct domain be specifed in the "sites" table via the admin interface.
