from django.conf.urls.defaults import patterns, url
from django.shortcuts import *
from django.http import *

import django_cim_forms.views

# this application has a custom view...
# specifying a string is the equivalent of passing a value to the 'shortName' paremater of HTTPGet

def view_model_by_acronym(request, model_acronym=None):
    get = request.GET.copy()
    if model_acronym:
        get.update({"shortName" : model_acronym})
        request.GET = get
    return django_cim_forms.views.detail(request,"dycoremodel","dycore",None)

urlpatterns = patterns('',
    url(r'^metadata/dycore/dycoremodel/(?P<model_acronym>[-_\w]+)/$',view_model_by_acronym),

)

# these fns would fail if run before the db tables were finalized (as would happen while running syncdb)
# using a try/except block worked for MySQL & Sqlite3 but not for POSTGreSQL
# so, as suggested in http://stackoverflow.com/questions/3599959/how-not-to-run-django-code-on-syncdb,
# I am calling it from urls.py
#setup_dycoremodel()
#setup_dycorescientificproperties_cv()
#setup_dycoreforms()
