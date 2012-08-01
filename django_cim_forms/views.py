#    Django-CIM-Forms
#    Copyright (c) 2012 CoG. All rights reserved.
#
#    Developed by: Earth System CoG
#    University of Colorado, Boulder
#    http://cires.colorado.edu/
#
#    This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].

# module imports
from django.template import *
from django.shortcuts import *
from django.http import *

from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from uuid import uuid4

from django.utils.encoding import smart_str

from django.conf import settings

from django_cim_forms.models import *
from django_cim_forms.forms import *
from django_cim_forms.helpers import *


def index(request):
    return HttpResponse("this is the index page for the django_cim_forms application")

#############################################################################################
# used by AJAX to generate a ModelChoiceField                                               #
# populates the field with all members of the class corresponding to the field of the model #
# that the model instance does not already have a relationship to                           #
#############################################################################################

def add_form(request):
    guid = request.GET.get('g',None)
    app = request.GET.get('a', None)
    model = request.GET.get('m', None)
    field = request.GET.get('f', None)

    if None in [guid,app,model,field]:
        msg = "invalid or incomplete guid/app/model/field combination"
        return HttpResponseBadRequest(msg)
    ModelType  = ContentType.objects.get(app_label=app.lower(),model=model.lower())
    ModelClass = ModelType.model_class()

    try:
        modelInstance = ModelClass.objects.get(_guid=guid)
        modelField = modelInstance.getField(field)
        ModelClassToAdd = modelField.getTargetModelClass()
        #TODO: DOUBLE-CHECK THAT THIS WORKS WITH FOREIGNKEY
        #TODO: ADDING THE .all() FN MADE IT WORK FOR MANYTOMANY
        modelsToExclude = [model.getGuid() for model in getattr(modelInstance,field).all()]
        #queryset = ModelClassToAdd.objects.exclude(guid__in=modelsToExclude)
        queryset = ModelClassToAdd.objects.filter(app=app).exclude(_guid__in=modelsToExclude)
        
    except ModelClass.DoesNotExist:
        modelInstance = ModelClass()
        modelField = modelInstance.getField(field)
        ModelClassToAdd = modelField.getTargetModelClass()
        # again, filtering by app
        queryset = ModelClassToAdd.objects.filter(app=app)
    
    class _AddForm(ModelForm):
        class Meta:
            model = ModelClass
            fields = (str(field),)
        def __init__(self,*args,**kwargs):
            qs=kwargs.pop("qs",None)
            super(_AddForm,self).__init__(*args,**kwargs)
            self.fields[field].queryset = qs

    form = _AddForm(instance=None,qs=queryset)
    formTemplate = Template("<p>Please select an instance of {{name}}:</p>{%for field in form.visible_fields %} {{ field }} {% endfor %}")
    formContext  = Context({"form" : form, "name" : modelField.getVerboseName()})

    return HttpResponse(formTemplate.render(formContext));


###################################################
# another view for AJAX.                          #
# having selected a model to add,                 #
# this function returns the content of that model #
###################################################

def get_content(request):
    guid = request.GET.get('g',None)
    app = request.GET.get('a', None)
    model = request.GET.get('m', None)
    field = request.GET.get('f', None)
    id = request.GET.get('i',None)

    if None in [guid,app,model,field,id]:
        msg = "invalid or incomplete guid/app/model/field/id combination"
        return HttpResponseBadRequest(msg)

    ModelType  = ContentType.objects.get(app_label=app.lower(),model=model.lower())
    ModelClass = ModelType.model_class()
    modelInstance = ModelClass()
    modelField = modelInstance.getField(field)
    ModelClassToAdd = modelField.getTargetModelClass()

    try:
        modelToAdd = ModelClassToAdd.objects.get(id=id)
    except ModelClassToAdd.DoesNotExist:
        msg = "unable to locate %s with id '%s'" % (ModelClassToAdd.getName(),id)
        return HttpResponseBadRequest(msg)

    json_data = modelToAdd.serialize(format="json")
    return HttpResponse(json_data);


############################################
# create, display, or edit a MetadataModel #
############################################

#@login_required
def detail(request, model_name, app_name="django_cim_forms", model_id=None):    

    # get the model & form...
    try:
        ModelType  = ContentType.objects.get(app_label=app_name.lower(),model=model_name.lower())
    except ObjectDoesNotExist:
        msg = "The model type '%s' does not exist in the application/project '%s'." % (model_name, app_name)
        return HttpResponseBadRequest(msg)

    ModelClass = ModelType.model_class()
    FormClass  = getFormClassFromModelClass(ModelClass)

    # sanity checks on the model & form...
    if not(ModelClass and issubclass(ModelClass,MetadataModel)):
        msg = "The model type '%s' is not an editable CIM Document." % model_name
        return HttpResponseBadRequest(msg)
    if not(FormClass and issubclass(FormClass,MetadataForm)):
        msg = "The system is unable to locate a metadata form bound to the model type '%s'." % model_name
        return HttpResponseBadRequest(msg)

    # using a global variable goes out of scope
    # so setting a class variable to track the current application of all models created
    # relationships are restricted to inter (not intra) app models
    MetadataModel.CURRENT_APP = app_name.lower()

    if request.GET:
        filter_args = {}
        error_msg = ""
        for (key,value) in request.GET.iteritems():
            error_msg += "%s='%s'," % (key,value)
            key = key + "__iexact"  # this ensures that the filter is case-insenstive
            filter_args[key] = value
        
        models = ModelClass.objects.filter(**filter_args)
        if len(models) != 1:
            msg = "The system cannot find a '%s' with the following properties: %s." % (model_name, error_msg.rstrip(","))
            return HttpResponseBadRequest(msg)
        else:
            model = models[0]
    
    else:
        if model_id:
            # try to load the specified model...
            #model = get_object_or_404(ModelClass, pk=model_id)
            try:
                model = ModelClass.objects.get(pk=model_id)
            except ModelClass.DoesNotExist:
                msg = "The system is unable to find a '%s' with an id of '%s'." % (model_name, model_id)
                return HttpResponseBadRequest(msg)
        else:
            # or just create a new one...
            model = ModelClass()


##    # check if the model should be rendered in a raw format,
##    # instead of via a webform...
##    format = request.GET.get('format',None)
##    if format:
##        if format.lower() == 'xml':
##            return serialize(request,model,format="xml")
##        elif format.lower() == 'json':
##            return serialize(request,model,format="json")
##        else:
##            msg = "invalid metadata format: %s" % (format)
##            return HttpResponseBadRequest(msg)

    # is this this an update of an existing model or a new submission?
    initialize = not(model.id)


    # BEFORE PROCEEDING WITH THIS VIEW,
    # LET'S MAKE SURE THAT THE USER IS AUTHORIZED TO VIEW/EDIT THE MODEL...
    if not request.user.is_authenticated():
        # if the user is not logged in, then redirect the user to the login screen and then come back
        return HttpResponseRedirect('%s/?next=%s' % (settings.LOGIN_URL,request.path))
    else:
        # TODO: SEPARATE THIS OUT INTO USER/ADMIN PERMISSION FOR GET/POST VIEW
        # if the user is logged in, then check that he has the right permissions
        permission_string = u"%s.%s_user_permission" % (model._cimDocumentProjectRestriction._meta.app_label,model._cimDocumentProjectRestriction.short_name.lower())
        if not request.user.has_perm("permission_string"):
            msg = "Permission Denied"
            return HttpResponseForbidden(msg)
        pass

    if request.method == 'POST':

## I AM NOW AUTHENTICATING ON GET & POST; SO THIS CODE IS NOT NEEDED (IT IS REPLACED BY THE BLOCK ABOVE)
##        # only logged in users can submit a form
##        if not request.user.is_authenticated():
##            request.session['_old_post'] = request.POST
##            request.session.modified = True
##            return HttpResponseRedirect('%s/?next=%s' % (settings.LOGIN_URL,request.path))
##        try:
##            # the user wasn't logged in when submitting the post
##            # so copy over the saved data
##            request.POST = request.session['_old_post']
##            del(request.session['_old_post'])
##        except KeyError:
##            # the user must have already been logged in when submitting the post
##            request.session.modified = False
##            pass
        
        form = FormClass(request.POST,instance=model,request=request)
        if form.is_valid():
            model = form.save(commit=False)
            if not(initialize):
                # create new (rather than update existing) model
                model.save(force_insert=True)
                form.save_m2m()
            else:            
                model.save()
                form.save_m2m()

            if model.isCIMDocument():
                # serialize to CIM
                xml_template_path = "%s/xml/%s.xml" % (app_name.lower(), model_name.lower())
                serializedModel = render_to_string(xml_template_path, {"model" : model, "type" : model.getCIMDocumentType()})

                # and publish to ATOM feed
                try:
                    ## TODO: THE FEED SETUP BY NCAR CANNOT HAVE SUBDIRECTORIES
                    ##documentFeedDirectory = settings.ATOM_FEED_DIR + "/" + app_name.lower() + "/" + model_name.lower()
                    documentFeedDirectory = settings.ATOM_FEED_DIR
                    documentFeedFile = model.getCIMDocumentName() + ".xml"
                    with open(documentFeedDirectory + "/" + documentFeedFile, 'w') as file:
                        # the smart_str ensures it is encoded as ASCII
                        # unicode and ATOM don't always play together well
                        file.write(smart_str(serializedModel))
                    file.closed
                except AttributeError:
                    msg = "unable to locate ATOM_FEED_DIR"
                    print msg
                except IOError:
                    msg = "unable to serialize model ('%s') to '%s'" % (documentFeedFile,documentFeedDirectory)
                    # just raise an error, rather than interfere w/ the HTTP request
                    #return HttpResponseBadRequest(msg)
                    print msg

            return HttpResponseRedirect(reverse('django_cim_forms.views.detail', args=(app_name,model_name,model.id)))
        else:
            print "invalid!"
    else:
        form = FormClass(instance=model,request=request,initialize=initialize)

    return render_to_response('django_cim_forms/metadata_detail.html', {'form' : form}, context_instance=RequestContext(request))


def serialize(request, model_name, app_name="django_cim_forms", model_id=None, format=None):
    # same as above, get the requested model
    # but then render it as CIM XML

    try:
        ModelType  = ContentType.objects.get(app_label=app_name.lower(),model=model_name.lower())
    except ObjectDoesNotExist:
        msg = "The model type '%s' does not exist in the application/project '%s'." % (model_name, app_name)
        return HttpResponseBadRequest(msg)

    ModelClass = ModelType.model_class()

    if not(ModelClass and issubclass(ModelClass,MetadataModel)):
        msg = "The model type '%s' is not an editable CIM Document." % model_name
        return HttpResponseBadRequest(msg)

    MetadataModel.CURRENT_APP = app_name.lower()
    if model_id:
        # try to load the specified model...
        #model = get_object_or_404(ModelClass, pk=model_id)
        try:
            model = ModelClass.objects.get(pk=model_id)
        except ModelClass.DoesNotExist:
            msg = "The system is unable to find a '%s' with an id of '%s'." % (model_name, model_id)
            return HttpResponseBadRequest(msg)
    else:
        # or just create a new one...
        model = ModelClass()

    if format:
        if format.lower() == 'xml':
            serializedModel = model.serialize(format='xml')
        elif format.lower() == 'json':
            serializedModel = model.serialize(format="json")
        else:
            msg = "The system cannot serialize to the metadata format: %s" % (format)
            return HttpResponseBadRequest(msg)

    # xml templates are stored as static files...
    # (the static location must be added to TEMPLATE_DIRS in settings.py)
    xml_template_path = "%s/xml/%s.xml" % (app_name.lower(), model_name.lower())
    renderedModel = render_to_string(xml_template_path, {"model" : model, "type" : "modelComponent"})
    return HttpResponse(renderedModel,mimetype="text/xml")

