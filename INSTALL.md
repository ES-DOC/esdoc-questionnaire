# INSTALLATION INSTRUCTIONS

The following instructions describe how to install the CIM Questionnaire on a Unix-type server (Cent-OS, Linux, Mac-OSX) for the purpose of starting to use and test the web application. 

## PRE-REQUISITES

The system must have the following Python packages installed:

* Python 2.7.2+
* Django 1.6.5
* South
* libXML (pip install lxml)
* pytz (pip install pytz)
* mptt (pip install django-mptt)
* python-memcached (pip install python-memcached)
* PIL (pip install pillow)
* A PostGres database is recommended.  However, Django also supports MySQL and SQLite3.
    * To use PostGres you must install psycopg2.

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
port=112111

[email]
host=smtp.gmail.com
port=
username=
password=

[site]
name=localhost

[settings]
secret_key=
static_root=static/

[debug]
debug=true
debug_toolbar=false
debug_profiling=false
```

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
