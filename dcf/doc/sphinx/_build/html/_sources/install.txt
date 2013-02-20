Installation
============

Django-CIM-Forms (DCF) is a Django Application.  It therefore must be installed into a Django Project.

Additionally, it requires several third-party Python packages and JQuery plugins (these latter are distributed with the application).  A virtual environment is recommended for DCF but not necesary.

Requirements
------------

1. Python 2.6+
2. Django 1.4+
3. lxml 2.3.3+
4. distribute (used for installing DCF)
5. pip (used for installing DCF)
6. south (used for upgrading DCF)
7. hotshot (used for profiling during development; should not be required for deployment)

Instructions
------------

1. use pip to install the desired version of DCF:

   pip install -I https://github.com/ES-DOC/django-cim-forms/raw/master/dist/django-cim-forms-<version>.tar.gz

   (You can use the "--no-deps" flag if you do not wish to reinstall any of the above dependencies that may already exist on your system.)

2. In the Django project hosting DCF, modify "settings.py" as follows:

    add 'dcf', 'dcf.cim_1_5' to INSTALLED_APPS
    add the location of static files (for example, rel('static/')) to TEMPLATE_DIRS

3. In the Django project hosting DCF, modify "urls.py" as follows:

    add "(r'^dcf/', include('dcf.urls')), to the list of pattersn


