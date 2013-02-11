#    Django-CIM-Forms
#    Copyright (c) 2012 CoG. All rights reserved.
#
#    Developed by: Earth System CoG
#    University of Colorado, Boulder
#    http://cires.colorado.edu/
#
#    This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].

from django.contrib import admin

from models import *

################################################################################################
# this admin function gets rid of "dangling" properties; properties that no models reference   #
# every property maintains a set of model class names that can reference it, (that list is set #
# explicitly in the property's __init__ fn, as well as dynamically when a model is initialized #
# with a set of properties).  this code checks the objects of each named class to see if the   #
# selected property is referenced by it.  if no named models reference the property, it can be #
# safely deleted from the db.                                                                  #
################################################################################################


def delete_danglers(modeladmin, request, queryset):

    for property in queryset:
        property_dangles = True
        for referencingModel in property.getReferencingModels():
            (app_name,model_name) = referencingModel.split('.')
            try:
                ModelType  = ContentType.objects.get(app_label=app_name.lower(),model=model_name.lower())
            except ObjectDoesNotExist:
                msg = "invalid model type '%s' in application '%s'" % (model_name, app_name)
                return MetadataError(msg)
            ModelClass = ModelType.model_class()
            # this assumes that the model field referencing the property is called "properties"
            # ...that a pretty big assumption
            if ModelClass.objects.filter(properties__id=property.id).exists():
                property_dangles = False
                # as soon as I find a model that references this property, there's no point in continuing
                break
        if property_dangles:
            property.delete()


delete_danglers.short_description = "Delete any of the selected properties that are not currently referenced by a model"

class PropertyAdmin(admin.ModelAdmin):
    actions = [delete_danglers]

# registration must be done w/ _concrete_ classes in their own applications
#admin.site.register(MetadataProperty, PropertyAdmin)
