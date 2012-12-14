from django.db import models

from django_cim_forms.models import *

class SoftwareComponent(MetadataModel):

    class Meta:
        abstract = False

    _name = "SoftwareComponent"
    _title = "Software Component"

    def __init__(self,*args,**kwargs):
        super(SoftwareComponent,self).__init__(*args,**kwargs)

    def __unicode__(self):
        name = u'%s' % self._title

        return name



