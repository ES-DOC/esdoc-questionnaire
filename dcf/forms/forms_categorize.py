
####################
#   Django-CIM-Forms
#   Copyright (c) 2012 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Feb 6, 2013 1:15:21 AM"

"""
.. module:: forms_categorize

Summary of module goes here

"""

from django.forms import *

from dcf.models import *
from dcf.utils  import *
from dcf.fields import *

class MetadataAttributeCategoryForm(ModelForm):
    class Meta:
        model   = MetadataAttributeCategory
        exclude = ('key','mapping')

    def __init__(self,*args,**kwargs):
        super(MetadataPropertyCategoryForm,self).__init__(*args,**kwargs)
        self.fields["name"].widget.attrs["readonly"] = True
        self.fields["order"].widget.attrs["size"] = 2
        self.fields["description"].widget.attrs["rows"] = 2
        self.fields["order"].widget.attrs["readonly"] = True
        update_field_widget_attributes(self.fields["name"],{"class":"readonly"})
        update_field_widget_attributes(self.fields["order"],{"class":"readonly"})

class MetadataPropertyCategoryForm(ModelForm):
    class Meta:
        model   = MetadataPropertyCategory
        exclude = ('key','mapping')

    def __init__(self,*args,**kwargs):
        super(MetadataPropertyCategoryForm,self).__init__(*args,**kwargs)
        self.fields["name"].widget.attrs["readonly"] = True
        self.fields["order"].widget.attrs["size"] = 2
        self.fields["description"].widget.attrs["rows"] = 2
        self.fields["order"].widget.attrs["readonly"] = True
        update_field_widget_attributes(self.fields["name"],{"class":"readonly"})
        update_field_widget_attributes(self.fields["order"],{"class":"readonly"})

# I THINK I ONLY HAVE TO USE THIS FORM
# (WHICH WORKS ON THE ABSTRACT METADATACATEGORY FORM)
# FOR EITHER ATTRIBUTES OR PROPERTIES
class MetadataCategoryForm(ModelForm):
    class Meta:
        model   = MetadataCategory
        exclude = ('key','mapping')

    def __init__(self,*args,**kwargs):
        super(MetadataCategoryForm,self).__init__(*args,**kwargs)
        self.fields["name"].widget.attrs["readonly"] = True
        self.fields["order"].widget.attrs["size"] = 2
        self.fields["description"].widget.attrs["rows"] = 2
        self.fields["order"].widget.attrs["readonly"] = True
        update_field_widget_attributes(self.fields["name"],{"class":"readonly"})
        update_field_widget_attributes(self.fields["order"],{"class":"readonly"})
