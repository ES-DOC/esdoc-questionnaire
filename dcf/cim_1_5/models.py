from django.db import models

from dcf.models import *

class SoftwareComponent(MetadataModel):

    class Meta:
        abstract = False

    _name = "SoftwareComponent"
    _title = "Software Component"

    foo = MetadataAtomicField.Factory("integerfield")
    bar = MetadataAtomicField.Factory("integerfield")
    baz = MetadataAtomicField.Factory("integerfield")

    def __init__(self,*args,**kwargs):
        super(SoftwareComponent,self).__init__(*args,**kwargs)

    def __unicode__(self):
        name = u'%s' % self._title
       
        return name



