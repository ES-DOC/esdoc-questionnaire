
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
__date__ ="Dec 18, 2013 1:19:49 PM"

"""
.. module:: questionnaire_model

Summary of module goes here

"""

from django.db                  import models
from django.contrib             import admin
from django.db.models.loading   import cache

from south.db                   import db

from questionnaire.utils        import *
from questionnaire.models       import *

from django.db import models


class MetadataModel(models.Model):
    # ideally, MetadataModel should be an ABC
    # but Django Models already have a metaclass: django.db.models.base.ModelBase
    # see http://stackoverflow.com/questions/8723639/a-django-model-that-subclasses-an-abc-gives-a-metaclass-conflict for a description of the problem
    # and http://code.activestate.com/recipes/204197-solving-the-metaclass-conflict/ for a solution that just isn't worth the hassle
    #from abc import *
    #__metaclass__ = ABCMeta
    class Meta:
        app_label   = APP_LABEL
        abstract    = True

    name         = models.CharField(max_length=SMALL_STRING,blank=False,null=False)
    description  = models.CharField(max_length=HUGE_STRING,blank=True,null=True)
    version      = models.ForeignKey("MetadataVersion",blank=False,null=True,related_name="models")
    order        = models.PositiveIntegerField(blank=True,null=True)

    parent_model = models.ForeignKey('self',null=True,blank=True,related_name="child_models")
    #child_models = models.ManyToManyField('self',related_name='parent_model')

    def add_child(self,child):
        # TODO: CHECK IT DOESN'T ALREADY EXIST
        #self.child_models.add(child)
        child.parent_model = self
        
    def get_children(self):
        return self.child_models.all()

    def get_parent(self):
        return self.parent_model

#    def get_descendents(self,descendents=[]):
#        children = self.get_children()
#        for child in children:
#            descendents.append(child)
#            child.get_descendents(descendents)
#        return descendents
#
#    def get_ancestors(self,ancestors=[]):
#        parent = self.get_parent()
#        if parent:
#            ancestores.append(parent)
#            parent.get_ancestors(ancestors)
#        return ancestors
    
#    def __unicode__(self):
#        return 'u%s::%s' % (self.version,self.name)

    @classmethod
    def factory(cls,model_name,model_fields={},overwrite_model=False,admin_access=False,*args,**kwargs):

        print kwargs
        
        model_name = model_name.encode("utf-8")  # just incase somebody passed in unicode instead of basic string

        model_attrs = {
            "__module__" : APP_LABEL + ".models",
        }
        model_attrs.update(model_fields)

        try:
            del cache.app_models[APP_LABEL][model_name]
        except KeyError:
            pass

        new_model = type(model_name, (MetadataModel,), model_attrs)

        new_model_fields    = [(field.name,field) for field in new_model._meta.fields]
        new_model_table     = new_model._meta.db_table

        for new_model_field in new_model_fields:
            try:
                print new_model_field[1].db_constraint
            except AttributeError:
                print u"no constraint for %s" % new_model_field[0]
    
        try:
            db.create_table(new_model_table,new_model_fields)
            db.execute_deferred_sql()
        except:
            if not overwrite_model:
                msg = "Error creating table '%s'.  Does it already exist?" % (new_model_table)
                raise QuestionnaireError(msg)
            
            
            # delete the table _completely_
            for new_model_field in new_model_fields:
                try:
                    if new_model_field[1].db_constraint:
                        try:
                            db.delete_unique(new_model_table,new_model_field[0])
                            print "deleted %s" % new_model_field[0]
                        except ValueError:
                            print "valueerror %s" % new_model_field[0]
                except AttributeError:
                    print "attributeerror %s" % new_model_field[0]
            db.delete_table(new_model_table)



            db.create_table(new_model_table,new_model_fields)
            db.execute_deferred_sql()
                
        
        if admin_access:
            for registered_model in admin.site._registry.keys():
                if new_model_table == registered_model._meta.db_table:
                    del admin.site._registry[registered_model]
                    break
                    


            class NewModelAdmin(admin.ModelAdmin):
                pass
            admin.site.register(new_model,NewModelAdmin)

        return new_model
