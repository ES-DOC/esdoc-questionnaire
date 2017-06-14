# INSTALLATION INSTRUCTIONS

The following instructions describe how to install the CIM Questionnaire on a Unix-type server (Cent-OS, Linux, Mac-OSX) for the purpose of starting to use and test the web application. 

## PRE-REQUISITES

The system must have the following Python packages installed:

* Python 2.7 (virtualenv --python=python2 <env dir>) [I AM NOT USING 3.4 UNTIL CONFIGPARSER IS COMPATABLE W/ THAT VERSION]
* Django 1.8.2 (pip install django==1.8.2)
* Django Rest Framework 3.5.0 (pip install djangorestframework==3.5.0)
* Django-Filters 0.15.3 (pip install django-filter==0.15.3)
* A PostGres database is recommended.  However, Django also supports MySQL and SQLite3.
    * To use PostGres you must install psycopg2 (pip install psycopg2)
* Django-Angular (pip install django-angular==0.8.4)
* Honeypot (pip install django-honeypot==0.5.0)
* Django-AllAuth (pip install django-allauth)
* Django Compressor (pip install django-compressor==1.5)
* JSONSchema (pip install jsonschema)
* Pillow (pip install Pillow==2.9.0; may require libjpeg-dev or other codecs)
* libXML (pip install lxml; may require libxml2-dev and/or libxslt1-dev)
* python-memcached (pip install python-memcached)
* pyesdoc

## DOWNLOAD

Download the software at the desired version from the github repository

## CONFIGURATION

* Generate a configuration file. The preferred location is ``$HOME/.config/esdoc-questionnaire.conf``. A custom location may be used in which case the ``settings.py`` variable ``CONF_PATH`` should be modified to match the location of the file. 
** a template is available in the repository's top-level director called ``esdoc-questionnaire.conf.TEMPLATE``
** a Django secret key can be generated at: http://www.miniwebtool.com/django-secret-key-generator/
* in some cases, compression of static files must be made explicit - uncomment out the relevant lines in "settings.py"
## INITIALIZATION

```sh
python Q/manage.py syncdb 
python Q/manage.py migrate
python Q/manage.py loaddata Q/questionnaire/fixtures/q_sites.json
python Q/manage.py loaddata Q/questionnaire/fixtures/q_synchronization.json
python Q/manage.py loaddata Q/questionnaire/fixtures/q_institutes.json
python Q/manage.py loaddate Q/mindmaps/fixtures/mindmap_sources.json
python Q/manage.py compress
python Q/manage.py collectstatic
```
