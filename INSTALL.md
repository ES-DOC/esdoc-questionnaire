# INSTALLATION INSTRUCTIONS

The following instructions describe how to install the CIM Questionnaire on a Unix-type server (Cent-OS, Linux, Mac-OSX) for the purpose of starting to use and test the web application. 

## PRE-REQUISITES

The system must have the following packages installed:

* Python 2.7 (virtualenv --python=python2 <env dir>) [I AM NOT USING 3.4 UNTIL CONFIGPARSER IS COMPATABLE W/ THAT VERSION]
* Celery 4.0.2 (for automated asynchronous task management)
* Django 1.8.2 (obviously)
* Django AllAuth 0.29.0 (for integrating Django's authentication system w/ OpenID)
* Django Angular 0.8.4 (for making Django Forms play nicely w/ AngularJS & Bootstrap)
* Django Celery Beat 1.0.1 (for making it easy to add period tasks to Celery)
* Django Compressor 1.5 (for compiling and compressing static files, including Less)
* Django Filter 0.15.3 (for creating custom filters to use w/ Django Rest Framework)
* Django Honeypot 0.5.0 (for preventing robots from accessing forms)
* Django Rest Framework 3.5.0 (for providing a RESTful API for Django models)
* JSON Schema 2.5.1 (for validating "qconfig" files)
* lxml 3.7.2 (for manipulating XML files) [MAY REQUIRE libxml2-dev AND/OR libxslt-dev]
* Pillow 2.9.0 (for manipulating images, such as project logos) [MAY REQUIRE libjpeg-dev OR OTHER CODECS]
* Python-memcached 1.54 (for caching objects in local memory)

* A PostGres database is recommended.  However, Django also supports MySQL and SQLite3.
    * To use PostGres you must install psycopg2
* A broker for celery is required.  RabbitMQ and Redis are supported.


## DOWNLOAD

Download/Clone the software at the desired version from the github repository

## CONFIGURATION

* Generate a configuration file. The preferred location is ``$HOME/.config/esdoc-questionnaire.conf``. A custom location may be used in which case the ``settings.py`` variable ``CONF_PATH`` should be modified to match the location of the file. 
** a template is available in the repository's top-level director called ``esdoc-questionnaire.conf.TEMPLATE``
** a Django secret key can be generated at: http://www.miniwebtool.com/django-secret-key-generator/
* in some cases, compression of static files must be made explicit - uncomment out the relevant lines in "settings.py"
* setup the celery task queue using redis or rabbitmq

## INITIALIZATION

```sh
python Q/manage.py syncdb 
python Q/manage.py migrate
python Q/manage.py loaddata Q/questionnaire/fixtures/q_sites.json
python Q/manage.py loaddata Q/questionnaire/fixtures/q_synchronization.json
python Q/manage.py loaddata Q/questionnaire/fixtures/q_institutes.json
python Q/manage.py loaddata Q/questionnaire/fixtures/q_tasks.json
python Q/manage.py loaddate Q/mindmaps/fixtures/mindmap_sources.json
python Q/manage.py compress
python Q/manage.py collectstatic
```
