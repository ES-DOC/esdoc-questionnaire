# module imports
from django.template import *
from django.shortcuts import *
from django.http import *

from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

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
        modelInstance = ModelClass.objects.get(guid=guid)
        modelField = modelInstance.getField(field)
        ModelClassToAdd = modelField.getTargetModelClass()

        #TODO: DOUBLE-CHECK THAT THIS WORKS WITH FOREIGNKEY
        #TODO: ADDING THE .all() FN MADE IT WORK FOR MANYTOMANY
        modelsToExclude = [model.guid for model in getattr(modelInstance,field).all()]

        #queryset = ModelClassToAdd.objects.exclude(guid__in=modelsToExclude)
        queryset = ModelClassToAdd.objects.filter(app=app).exclude(guid__in=modelsToExclude)
        
    except ModelClass.DoesNotExist:
        modelInstance = ModelClass()
        modelField = modelInstance.getField(field)
        ModelClassToAdd = modelField.getTargetModelClass()
        queryset = ModelClassToAdd.objects.all()
    
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

def detail(request, model_name, app_name="django_cim_forms", model_id=None):
    # get the model & form...
    try:
        ModelType  = ContentType.objects.get(app_label=app_name.lower(),model=model_name.lower())
    except ObjectDoesNotExist:
        msg = "invalid model type '%s' in application '%s'" % (model_name, app_name)
        return HttpResponseBadRequest(msg)

    ModelClass = ModelType.model_class()
    FormClass  = getFormClassFromModelClass(ModelClass)

    # sanity checks on the model & form...
    if not(ModelClass and issubclass(ModelClass,MetadataModel)):
        msg = "invalid model type: '%s'" % model_name
        return HttpResponseBadRequest(msg)
    if not(FormClass and issubclass(FormClass,MetadataForm)):
        msg = "cannot determine MetadataForm bound to model type: '%s'" % model_name
        return HttpResponseBadRequest(msg)

    # using a global variable goes out of scope
    # so setting a class variable to track the current application of all models created
    # relationships are restricted to inter (not intra) app models
    MetadataModel.CURRENT_APP = app_name.lower()
    
    if model_id:
        # try to load the specified model...
        #model = get_object_or_404(ModelClass, pk=model_id)
        try:
            model = ModelClass.objects.get(pk=model_id)
        except ModelClass.DoesNotExist:
            msg = "unable to find '%s' with id of '%s'" % (model_name, model_id)
            return HttpResponseBadRequest(msg)
    else:
        # or just create a new one...
        model = ModelClass()

    if request.method == 'POST':
        form = FormClass(request.POST,instance=model,request=request)
        if form.is_valid():
            model = form.save(commit=False)
            model.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse('django_cim_forms.views.detail', args=(app_name,model_name,model.id)))
        else:
            print "invalid!"
    else:
        # check if this the the first time I'm loading this model...
        initializeForm = not(model.id)
        form = FormClass(instance=model,request=request,initialize=initializeForm)
    
    return render_to_response('django_cim_forms/metadata_detail.html', {'form' : form}, context_instance=RequestContext(request))

