
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
__date__ ="Jun 12, 2013 12:18:10 PM"

"""
.. module:: forms_categorize

Summary of module goes here

"""
from django.forms import *

from dcf.models import *
from dcf.fields import *
from dcf.utils  import *

def save_standard_categories(standard_categories_data,project):

    for standard_category_data in standard_categories_data:

        standard_category   = MetadataStandardCategory.objects.get(pk=standard_category_data["pk"])

        # these are the only 3 fields that can change for standard categories
        new_name            = standard_category_data["fields"]["name"]
        new_order           = standard_category_data["fields"]["order"]
        new_description     = standard_category_data["fields"]["description"]

        if standard_category_data["fields"]["remove"] == "True":
            standard_category.delete()
        else:
            if (standard_category.name != new_name) or (standard_category.order != new_order) or (standard_category.description != new_description):
                standard_category.name          = new_name
                standard_category.order         = new_order
                standard_category.description   = new_description
                standard_category.save()

def save_scientific_categories(scientific_categories_data,project):

    for scientific_category_data in scientific_categories_data:

        try:
            scientific_category = MetadataScientificCategory.objects.get(pk=scientific_category_data["pk"])
        except ObjectDoesNotExist:
            scientific_category = MetadataScientificCategory(
                project=project,
                component_name=scientific_category_data["fields"]["component_name"],
                key=scientific_category_data["fields"]["key"],
            )

        # these are the only 3 fields that can change for standard categories
        new_name            = scientific_category_data["fields"]["name"]
        new_order           = scientific_category_data["fields"]["order"]
        new_description     = scientific_category_data["fields"]["description"]

        if scientific_category_data["fields"]["remove"] == "True":
            # TODO: ADD A TRY/CATCH HERE!!!!!
            if scientific_category.pk:
                scientific_category.delete()
        else:
            if (scientific_category.name != new_name) or (scientific_category.order != new_order) or (scientific_category.description != new_description):
                scientific_category.name          = new_name
                scientific_category.order         = new_order
                scientific_category.description   = new_description
                scientific_category.save()

class MetadataScientificCategoryForm(ModelForm):
    class Meta:
        model   = MetadataScientificCategory

    def __init__(self,*args,**kwargs):
        super(MetadataScientificCategoryForm,self).__init__(*args,**kwargs)

        self.fields["key"].widget               = HiddenInput()
        self.fields["component_name"].widget    = HiddenInput()
        self.fields["remove"].widget            = HiddenInput()

        self.fields["description"].widget.attrs["rows"] = 2
        self.fields["order"].widget.attrs["size"]       = 2
        self.fields["name"].widget.attrs["disabled"]    = "disabled"
        self.fields["order"].widget.attrs["disabled"]   = "disabled"

        update_field_widget_attributes(self.fields["name"],{"class":"readonly"})
        update_field_widget_attributes(self.fields["order"],{"class":"readonly"})

        