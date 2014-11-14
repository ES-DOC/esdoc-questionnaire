
####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Jan 5, 2014 4:09:29 PM"

"""
.. module:: forms_categorize

Summary of module goes here

"""

from django.forms import *

from CIM_Questionnaire.questionnaire.models.metadata_customizer import MetadataStandardCategoryCustomizer, MetadataScientificCategoryCustomizer
from CIM_Questionnaire.questionnaire.utils import update_field_widget_attributes, set_field_widget_attributes

class MetadataStandardCategoryCustomizerForm(ModelForm):

    class Meta:
        model   = MetadataStandardCategoryCustomizer

        fields  = [
                    # hidden fields...
                    "key",
                    # customizer fields...
                    "name","description","order",
                  ]

    hidden_fields       = ("key",)
    customizer_fields   = ("name","description","order",)

    def get_hidden_fields(self):
        return [field for field in self if field.name in self.hidden_fields]

    def get_customizer_fields(self):
        return [field for field in self if field.name in self.customizer_fields]

    def __init__(self,*args,**kwargs):
        super(MetadataStandardCategoryCustomizerForm,self).__init__(*args,**kwargs)

        #category_customizer = self.instance

        update_field_widget_attributes(self.fields["name"],{"readonly":"readonly","class":"readonly"})

        set_field_widget_attributes(self.fields["description"],{"cols":"60","rows":"4"})

        update_field_widget_attributes(self.fields["order"],{"readonly":"readonly","class":"readonly"})


class MetadataScientificCategoryCustomizerForm(ModelForm):

    class Meta:
        model   = MetadataScientificCategoryCustomizer

        fields  = [
                    # hidden fields...
                    "key",
                    # customizer fields...
                    "name","description","order"
                  ]

    hidden_fields       = ("key",)
    customizer_fields   = ("name","description","order",)

    def get_hidden_fields(self):
        return [field for field in self if field.name in self.hidden_fields]

    def get_customizer_fields(self):        
        return [field for field in self if field.name in self.customizer_fields]

    def __init__(self,*args,**kwargs):
        super(MetadataScientificCategoryCustomizerForm,self).__init__(*args,**kwargs)

        #category_customizer = self.instance

        set_field_widget_attributes(self.fields["description"],{"cols":"60","rows":"4"})

        update_field_widget_attributes(self.fields["order"],{"readonly":"readonly","class":"readonly"})
