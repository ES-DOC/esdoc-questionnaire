
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
__date__ ="Jan 31, 2013 12:45:47 PM"

"""
.. module:: views_index

Summary of module goes here

"""

from django.template import *
from django.shortcuts import *
from django.http import *

from django.utils import simplejson as json
from django.forms import *

import re


from dcf.views.views_error import error
from dcf.utils import *
from dcf.models import *

def index(request):

    allVersions =   MetadataVersion.objects.all()
    version = allVersions[0]
    categorization = version.default_categorization

    # HERE IS HOW I CAN GET A REVERSE RELATIONSHIP !!!
    #print categorization.version.all()
    # OR EVEN
    #print categorization.version.get(pk=1)

#    # AND HERE IS SOME MAGICAL EFFICIENT STUFF
#    # (CACHING DICTIONARY OF RELATIONSHIPS; USEFUL IN A VIEW?)
#    qs = MetadataCategorization.objects.all()
#    obj_dict = dict([(obj.id, obj) for obj in qs])
#    objects = MetadataVersion.objects.filter(default_categorization__in=qs)
#    relation_dict = {}
#    for obj in objects:
#        relation_dict.setdefault(obj.id, []).append(obj)
#    for id, related_items in relation_dict.items():
#        obj_dict[id].related_items = related_items

#    print "\nfor foreign keys..."
#    print "dict of relationships (version.id : categorization): %s" % obj_dict
#    print "dict of reverse relationships (categorization.id : [list of versions]): %s" % relation_dict

#    project = MetadataProject.objects.get(pk=1)
#    print "project: %s" % project
#    print "project.default_version: %s" % project.default_version
#    print "project.versions: %s" % project.versions.all()
#    print "versions that are the default of this project: %s" % MetadataVersion.objects.filter(project=project)
#    print "versions that are possible for this project: %s" % MetadataVersion.objects.filter(metadataproject=project)
#
#    version1 = version
#    version2 = allVersions[1]
#    print "v1=%s" % version1
#    print "v2=%s" % version2
#    print "projects that have v1 as default: %s" % version1.getDefaultProjects()#project.all()
#    print "projects that have v2 as default: %s" % version2.getDefaultProjects()#project.all()
#    print "projects that have v1 as possible: %s" % version1.getProjects()#metadataproject_set.all()
#    print "projects that have v2 as possible: %s" % version2.getProjects()#metadataproject_set.all()


    allVersions         = MetadataVersion.objects.all()
    allCategorizations  = MetadataCategorization.objects.all()
    allVocabularies     = MetadataVocabulary.objects.all()
    allProjects         = MetadataProject.objects.all()
    allCustomizations   = MetadataModelCustomizer.objects.all()

    allModels   = set([model.getName() for model in get_subclasses(MetadataModel) if model._isCIMDocument])

    class _IndexForm(forms.Form):
        class Meta:
            fields  = ("versions","categorizations","projects","vocabularies","customizations","models","action")

        versions        = ModelChoiceField(queryset=allVersions,label="Metadata Version",required=False)
        categorizations = ModelChoiceField(queryset=allCategorizations,label="Associated Categorization",required=False)
        projects        = ModelChoiceField(queryset=allProjects,label="Metadata Project",required=True)
        vocabularies    = ModelMultipleChoiceField(queryset=allVocabularies,label="Associated Vocabularies",required=False)
        customizations  = ModelChoiceField(queryset=allCustomizations,label="Form Customization",required=False)

        models          = ChoiceField(label="Metadata Model",required=False)
        models.choices  = [(model_name.lower(),model_name) for model_name in allModels]
        action          = CharField(max_length=LIL_STRING)

        def __init__(self,*args,**kwargs):
            super(_IndexForm,self).__init__(*args,**kwargs)

            update_field_widget_attributes(self.fields["versions"],{"onchange":"reset_options(this);"})
            update_field_widget_attributes(self.fields["categorizations"],{"onchange":"reset_options(this);"})
            update_field_widget_attributes(self.fields["projects"],{"onchange":"reset_options(this);"})
            update_field_widget_attributes(self.fields["vocabularies"],{"onchange":"reset_options(this);"})
            update_field_widget_attributes(self.fields["customizations"],{"onchange":"reset_options(this);"})
            update_field_widget_attributes(self.fields["models"],{"onchange":"reset_options(this);"})

    data = "{ \"versions\" : %s, \"categorizations\" : %s, \"vocabularies\" : %s, \"projects\" : %s, \"customizations\" : %s }" % \
        (JSON_SERIALIZER.serialize(allVersions),
        JSON_SERIALIZER.serialize(allCategorizations),
        JSON_SERIALIZER.serialize(allVocabularies),
        JSON_SERIALIZER.serialize(allProjects),
        JSON_SERIALIZER.serialize(allCustomizations))

    if request.method == "POST":
        form = _IndexForm(request.POST)
        if form.is_valid():
            action          = form.cleaned_data["action"]
            version         = form.cleaned_data["versions"]
            categorization  = form.cleaned_data["categorizations"]
            project         = form.cleaned_data["projects"]
            vocabulary      = form.cleaned_data["vocabularies"]
            customization   = form.cleaned_data["customizations"]
            model           = form.cleaned_data["models"]
            parameters      = ""

            if not action in ["customize","edit","test"]:
                msg = "unknown action: %s" % action
                return error(request,msg)


            if version:
                version_number = version.version
            elif project.default_version:
                version_number = project.default_version.version
            else:
                msg = "%s has no default version; please specify one" % project
                return error(request,msg)
            if customization and action == "customize":
                parameters = "?name=%s" % customization.name

            # url should be "action/version/project/name[?name=customization.name]
            url = "%s/%s/%s/%s/%s" % (action,version_number,project.name,model,parameters)
            return HttpResponseRedirect(url)

            pass
    else:
        form = _IndexForm()
    
    return render_to_response('dcf/dcf_index.html', {"form":form,"data":data}, context_instance=RequestContext(request))

