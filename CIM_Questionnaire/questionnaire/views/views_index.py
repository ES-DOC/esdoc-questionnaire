
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
__date__ ="Sep 30, 2013 3:04:42 PM"

"""
.. module:: views

Summary of module goes here

"""

from questionnaire.views import *

from django.forms import *

def index(request):

    class _IndexForm(forms.Form):
        class Meta:
            pass

#        projects        = ModelChoiceField()
#        versions        = ModelChoiceField()
#        vocabularies    = ModelMultipleChoiceField()
#        customizations  = ModelChoiceField()
#        models          = ModelChoiceField()
        action          = CharField(max_length=64)

        def __init__(self,*args,**kwargs):
            super(_IndexForm,self).__init__(*args,**kwargs)

    if request.method == "POST":
        form = _IndexForm(request.POST)
        print form
    else: # request.method == "GET":
        form = _IndexForm()
      
    return render_to_response('questionnaire/questionnaire_index.html', {'form' : form}, context_instance=RequestContext(request))

#
#    allVersions         = MetadataVersion.objects.all()
#    allCategorizations  = MetadataCategorization.objects.all()
#    allVocabularies     = MetadataVocabulary.objects.all()
#    allProjects         = MetadataProject.objects.all()
#    allCustomizations   = MetadataModelCustomizer.objects.all()
#
#    allModels   = set([model.getName() for model in get_subclasses(MetadataModel) if model._is_metadata_document])
#
#    class _IndexForm(forms.Form):
#        class Meta:
#            fields  = ("versions","categorizations","vocabularies","projects","customizations","models","action")
#
#        versions        = ModelChoiceField(queryset=allVersions,label="Metadata Version",required=False)
#        categorizations = ModelChoiceField(queryset=allCategorizations,label="Associated Categorization",required=False)
#        vocabularies    = ModelMultipleChoiceField(queryset=allVocabularies,label="Associated Vocabularies",required=False)
#        projects        = ModelChoiceField(queryset=allProjects,label="Metadata Project",required=True)
#        customizations  = ModelChoiceField(queryset=allCustomizations,label="Form Customization",required=False)
#
#        models          = ChoiceField(label="Metadata Model",required=False)
#        models.choices  = [(model_name.lower(),model_name) for model_name in allModels]
#        action          = CharField(max_length=LIL_STRING)
#
#        def __init__(self,*args,**kwargs):
#            super(_IndexForm,self).__init__(*args,**kwargs)
#
#            update_field_widget_attributes(self.fields["versions"],{"onchange":"reset_options(this);"})
#            update_field_widget_attributes(self.fields["categorizations"],{"onchange":"reset_options(this);"})
#            update_field_widget_attributes(self.fields["projects"],{"onchange":"reset_options(this);"})
#            update_field_widget_attributes(self.fields["vocabularies"],{"onchange":"reset_options(this);"})
#            update_field_widget_attributes(self.fields["customizations"],{"onchange":"reset_options(this);"})
#            update_field_widget_attributes(self.fields["models"],{"onchange":"reset_options(this);"})
#
#    data = "{ \"versions\" : %s, \"categorizations\" : %s, \"vocabularies\" : %s, \"projects\" : %s, \"customizations\" : %s }" % ( \
#        JSON_SERIALIZER.serialize(allVersions),
#        JSON_SERIALIZER.serialize(allCategorizations),
#        JSON_SERIALIZER.serialize(allVocabularies),
#        JSON_SERIALIZER.serialize(allProjects),
#        JSON_SERIALIZER.serialize(allCustomizations)
#    )
#
#    if request.method == "POST":
#        form = _IndexForm(request.POST)
#        if form.is_valid():
#            action          = form.cleaned_data["action"]
#            version         = form.cleaned_data["versions"]
#            categorization  = form.cleaned_data["categorizations"]
#            vocabulary      = form.cleaned_data["vocabularies"]
#            project         = form.cleaned_data["projects"]
#            customization   = form.cleaned_data["customizations"]
#            model           = form.cleaned_data["models"]
#            parameters      = ""
#
#            if not action in ["customize","edit","test"]:
#                msg = "unknown action: %s" % action
#                return error(request,msg)
#
#            if version:
#                version_number = version.version
#            if customization and action == "customize":
#                parameters = "?name=%s" % customization.name
#
#            url = "%s/%s/%s/%s/%s" % (action,project.name,model,version_number,parameters)
#            return HttpResponseRedirect(url)
#
#    else:
#        form = _IndexForm()
#
#    return render_to_response('dcf/dcf_index.html', {"form":form,"data":data}, context_instance=RequestContext(request))


