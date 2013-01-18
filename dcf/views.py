# module imports
from django.template import *
from django.shortcuts import *
from django.http import *

from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType

from django.core.exceptions import ObjectDoesNotExist, FieldError, MultipleObjectsReturned
from django.db import IntegrityError

from django.utils import simplejson as json

from django.conf import settings

from dcf.models import *
from dcf.forms import *
from dcf.helpers import *

def index(request):
    return HttpResponse("this is the index page for the django_cim_forms application")

##########################################
# display instructions for the edit form #
##########################################

def edit_instructions(request):

    return render_to_response('dcf/metadata_edit_instructions.html', {}, context_instance=RequestContext(request))

###############################################
# display instructions for the customize form #
###############################################

def customize_instructions(request):

    return render_to_response('dcf/metadata_customize_instructions.html', {}, context_instance=RequestContext(request))

##############################
# display the customize form #
##############################

def customize(request, model_name, app_name):

    model_name = model_name.lower()
    app_name = app_name.lower()
    msg = ""
  
    # get the requested model...
    try:
        ModelType  = ContentType.objects.get(app_label=app_name,model=model_name)
    except ObjectDoesNotExist:
        msg = "The model type '%s' does not exist in the application/project '%s'." % (model_name, app_name)
        return HttpResponseBadRequest(msg)

    ModelClass = ModelType.model_class()   
    
    # sanity checks on the model...
    if not(ModelClass and issubclass(ModelClass,MetadataModel)):
        msg = "The model type '%s' is not an editable CIM class." % model_name
        return HttpResponseBadRequest(msg)

    # get the customizer for this model/app combination
    # (other filters may have been passed in as HTTP parameters)
    filterParameters = {}
    if request.GET:
        for (key,value) in request.GET.iteritems():
            #key = key + "__iexact"  # this ensures that the filter is case-insenstive
            # unfortunately, the filter has to be case-sensitive b/c get_or_create() below _is_ case-sensitive
            # see https://code.djangoproject.com/ticket/7789 for more info
            if value.lower()=="true":
                filterParameters[key] = 1
            elif value.lower()=="false":
                filterParameters[key] = 0
            else:
                filterParameters[key] = re.sub('[\"\']','',value) # strip out any quotes
    filterParameters["appName"] = app_name
    filterParameters["modelName"] = model_name

    if len(filterParameters) > 2:
        # if there were (extra) filter parameters passed
        # then try to get the model w/ those parameters
        try:
            customizer = ModelCustomizer.objects.get(**filterParameters)
        except FieldError:
            # raise an error if some of the filter parameters were invalid
            msg = "Unable to create a ModelCustomizer with the following parameters: %s" % (", ").join([u'%s=%s'%(key,value) for (key,value) in filterParameters.iteritems()])
            return HttpResponseBadRequest(msg)
        except MultipleObjectsReturned:
            # raise an error if those filter params weren't enough to uniquely identify a model
            msg = "Unable to find a <i>single</i> ModelCustomizer with the following parameters: %s" % (", ").join([u'%s=%s'%(key,value) for (key,value) in filterParameters.iteritems()])
            return HttpResponseBadRequest(msg)
            # customizer = ModelCustomizer(**filterParameters)
        except IntegrityError:
            # raise an error
            msg = "Unable to find a <i>single</i> ModelCustomizer with the following parameters: %s" % (", ").join([u'%s=%s'%(key,value) for (key,value) in filterParameters.iteritems()])
            return HttpResponseBadRequest(msg)
            # customizer = ModelCustomizer(**filterParameters)
        except ModelCustomizer.DoesNotExist:
            # if there is nothing w/ those filter params, then create a new model/form
            customizer = ModelCustomizer(**filterParameters)


    else:
        # otherwise, return a new model/form
        customizer = ModelCustomizer(**filterParameters)
        
    if request.method == 'POST':

        # it's a bit unusual to pass request as a kwarg
        # but my forms have to initialize any subforms that they are comprised of
        # so I potentially need the HTTP POST data
        form = ModelCustomizerForm(request.POST,instance=customizer,request=request)

        if form.is_valid():
            model = form.save(commit=False)
            model.save()
            form.save_m2m()
            # after saving the form (ModelCustomizer & FieldCustomizers),
            # go ahead and save any changes made to FieldCategories by the form...
            expandedTags = json.loads(form.data["expandedTags"])
            for tagContents in expandedTags.itervalues():
                tagID = tagContents.pop("pk",None)
                if tagID:
                    try:
                        category = FieldCategory.objects.get(pk=tagID)
                        for (fieldName,fieldValue) in tagContents.iteritems():
                            setattr(category,fieldName,fieldValue)
                            category.save()
                    except: # catches both the category doesn't exist & the field doesn't exist error
                        pass

            msg = "Successfully saved the customization: '%s'." % model.name

        else:
            msg = "Unable to save the customization.  Please review the form and try again."

    else:

        form = ModelCustomizerForm(instance=customizer,request=request)

    return render_to_response('dcf/metadata_customize.html', 
        { "app_name" : app_name, "model_name" : model_name, "form" : form, "msg" : msg},
        context_instance=RequestContext(request))


#########################################
# display the edit form                 #
# (to create, edit, or display a model) #
#########################################

def edit(request, model_name, app_name):

    model_name = model_name.lower()
    app_name = app_name.lower()
    msg = ""

    # get the requested model...
    try:
        ModelType  = ContentType.objects.get(app_label=app_name,model=model_name)
    except ObjectDoesNotExist:
        msg = "The model type '%s' does not exist in the application/project '%s'." % (model_name, app_name)
        return HttpResponseBadRequest(msg)

    ModelClass = ModelType.model_class()

    # sanity checks on the model...
    if not(ModelClass and issubclass(ModelClass,MetadataModel)):
        msg = "The model type '%s' is not an editable CIM class." % model_name
        return HttpResponseBadRequest(msg)

    # filters may have been passed in as HTTP parameters
    filterParameters = {}
    if request.GET:
        for (key,value) in request.GET.iteritems():
            #key = key + "__iexact"  # this ensures that the filter is case-insenstive
            # unfortunately, the filter has to be case-sensitive b/c get_or_create() below _is_ case-sensitive
            # see https://code.djangoproject.com/ticket/7789 for more info
            if value.lower()=="true":
                filterParameters[key] = 1
            elif value.lower()=="false":
                filterParameters[key] = 0
            else:
                filterParameters[key] = re.sub('[\"\']','',value) # strip out any quotes

    if len(filterParameters) > 0:
        # if there were extra filter parameters passed
        # then try to get the model w/ those parameters
        try:
            model = ModelClass.objects.get(**filterParameters)
        except FieldError:
            # raise an error if some of the filter parameters were invalid
            msg = "Unable to find a '%s' with the following parameters: %s" % (ModelClass.getName(), (", ").join([u'%s=%s'%(key,value) for (key,value) in filterParameters.iteritems()]))
            return HttpResponseBadRequest(msg)
        except MultipleObjectsReturned:
            # raise an error if those filter params weren't enough to uniquely identify a model
            msg = "Unable to find a <i>single</i> '%s' with the following parameters: %s" % (ModelClass.getName(), (", ").join([u'%s=%s'%(key,value) for (key,value) in filterParameters.iteritems()]))
            return HttpResponseBadRequest(msg)
            # customizer = ModelCustomizer(**filterParameters)
        except IntegrityError:
            # raise an error
            msg = "Unable to find a <i>single</i> '%s' with the following parameters: %s" % (ModelClass.getName(), (", ").join([u'%s=%s'%(key,value) for (key,value) in filterParameters.iteritems()]))
            return HttpResponseBadRequest(msg)
        except ModelCustomizer.DoesNotExist:
            # if there is nothing w/ those filter params, then create a new model/form
            model = ModelClass(**filterParameters)
    else:
        # otherwise, just return a new model/form
        model = ModelClass()

    # get the customizer...
    customizers = ModelCustomizer.objects.filter(appName=app_name,modelName=model_name)
    if customizers:
        try:
            # TODO: WHERE IN THE HTTP REQUEST SHOULD I SPECIFY THE NAME OF THE CUSTOMIZER?
            customizer_name = "foobar"
            customizer = customizers.get(name=customizer_name)
        except MultipleObjectsReturned:
            # I don't expect to wind up here, but just in-case something weird happens go ahead and use the default customizer
            customizer = customizers.get(default=1)
        except ModelCustomizer.DoesNotExist:
            customizer = customizers.get(default=1)
    else:
        msg = "This form has not been customized.  Please contact the project administrator."
#        customizer = ModelCustomizer(appName=app_name,modelName=model_name)
        return HttpResponseBadRequest(msg)


    # use the customizer to create the form...
    FormClass = MetadataFormFactory(ModelClass,customizer)
    form = FormClass(instance=model,request=request)


    return render_to_response('dcf/metadata_edit.html',
        { "app_name" : app_name, "model_name" : model_name, "form" : form, "msg" : msg},
        context_instance=RequestContext(request))

############################################
# create, display, or edit a MetadataModel #
############################################

def detail(request, model_name, app_name, model_id=None):

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

    if request.GET:
        # the GET can include optional filters
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
            try:
                model = ModelClass.objects.get(pk=model_id)
            except ModelClass.DoesNotExist:
                msg = "The system is unable to find a '%s' with an id of '%s'." % (model_name, model_id)
                return HttpResponseBadRequest(msg)
        else:
            # or just create a new one...
            model = ModelClass()

    return render_to_response('dcf/metadata_detail.html', {}, context_instance=RequestContext(request))

##############
# AJAX views #
##############

def get_field_category(request):
    modelName = request.GET.get('m',None)
    appName = request.GET.get('a',None)
    fieldCategoryName = request.GET.get('n',None)
    fieldCategoryKey = request.GET.get('k',None)
    createIfNone = request.GET.get('c',True)

    if not (modelName and appName and fieldCategoryKey):
        msg = "invalid HTPP parameters to get_field_category"
        return HttpResponseBadRequest(msg)

    try:
        category = FieldCategory.objects.get(modelName=modelName,appName=appName,key=fieldCategoryKey)
    except FieldCategory.DoesNotExist:
        if createIfNone:
            category = FieldCategory.objects.create(modelName=modelName,appName=appName,name=fieldCategoryName,key=fieldCategoryKey)
        else:
            msg = "invalid HTPP parameters to get_field_category"
            return HttpResponseBadRequest(msg)

    json_category = JSON_SERIALIZER.serialize([category])
    return HttpResponse(json_category[1:len(json_category)-1], mimetype='application/json');


def delete_field_category(request):
    modelName = request.GET.get('m',None)
    appName = request.GET.get('a',None)
    fieldCategoryKey = request.GET.get('k',None)

    if not (modelName and appName and fieldCategoryKey):
        msg = "invalid HTPP parameters to delete_field_category"
        return HttpResponseBadRequest(msg)

    try:
        category = FieldCategory.objects.get(_model=modelName,_app=appName,key=fieldCategoryKey)
    except FieldCategory.DoesNotExist:
        msg = "invalid HTPP parameters to get_field_category"
        return HttpResponseBadRequest(msg)

    category.delete()

    # don't bother returning anything; if there was an error the above HttpResponseBadRequest would catch it
    return HttpResponse("");

def edit_field_category(request):
    # id is explicitly passed into request;
    # all the others are just copied over from the javascript category dictionary
    # (see below)
    fieldID = request.GET.get('i',None)

    try:
        category = FieldCategory.objects.get(pk=fieldID)
    except FieldCategory.DoesNotExist:
        msg = "invlaid HTPP parameters to edit_field_category"
        return HttpResponseBadRequest(msg)

    # override the existing category values with those from the javascript category dictionary (they are more current)
    for (key,value) in request.GET.iteritems():
        try:
            setattr(category, key, value);
        except:
            pass

    form = FieldCategoryForm(instance=category)

    formTemplate = Template("\
      <!-- don't need to re-load JS/CSS b/c it's already loaded in the parent page -->\
      <div id='metadata'>\
        <div id='customize'>\
            <form>\
                <br/>\
                <div class='form'>\
                    <table>\
                        {% for field in form.visible_fields %}\
                            <tr class='{% cycle \"odd\" \"even\" %}'>\
                                <td class='field-label'>{{field.label}}:&nbsp;</td>\
                                <td class='field-value'>\
                                    <div class='field' name='{{field.name}}'>\
                                        {{field}}\
                                    </div>\
                                </td>\
                            </tr>\
                        {% endfor %} {# /field in form.visible_fields #}\
                    </table>\
                </div> <!-- /.form -->\
            </form>\
        </div> <!-- /#customize -->\
      </div> <!-- /#metadata -->\
    ")
    formContext  = Context({"STATIC_URL" : "/static/", "form" : form, })
    #return render_to_response('dcf/metadata_field_category.html', formContext, context_instance=RequestContext(request))

    return HttpResponse(formTemplate.render(formContext))

def component_nest(request):

    guid = request.GET.get('guid',None)

    # TODO: get model based on guid
    # TODO: this is just sample data; ought to do a series of list comprehensions
    data = []
    data.append({
        "data" : "title: 1",
        "attr" : { "id" : "1", "rel" : "blarf"},
        "children" : []

    })
    data[-1]["children"].append({
        "data" : "title: 1.1",
        "attr" : { "id" : "1.1"}
    })
    data[-1]["children"].append({
        "data" : "title: 1.2",
        "attr" : { "id" : "1.2"}
    })
    data.append({
        "data" : "title: 2",
        "attr" : { "id" : "2"},
        "children" : []
    })
      
    return HttpResponse(simplejson.dumps(data), mimetype='application/json')