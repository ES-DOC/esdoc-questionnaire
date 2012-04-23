# module imports.
from django.template import *
from django.shortcuts import *
from django.http import *

from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core import serializers
from django.forms import *

# intra/inter-package imports.

from django_cim_forms.models import *
from django_cim_forms.forms import *
from django_cim_forms.helpers import *

def test(request):

    FormSet = modelformset_factory(Foo,extra=2)
    formset = FormSet(initial=[{"name":"ofsdafadf"}])
    
    return render_to_response('django_cim_forms/test.html', {"formset":formset}, context_instance=RequestContext(request))

def index(request):
    return HttpResponse("this is the index page for the metadata application")

def detail(request, model_name, app_name="django_cim_forms", model_id=None):
    
    # get the model & form...
    try:
        ModelType  = ContentType.objects.get(app_label=app_name,model=model_name.lower())
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


    if model_id:
        # try to load the specified model...
        #model = get_object_or_404(ModelClass, pk=model_id)
        try:
            model = ModelClass.objects.get(pk=model_id)
        except ModelClass.DoesNotExist:
            msg = "unable to find '%s' with id of '%s'" % (model_name, model_id)
            return HttpResponseBadRequest(msg)
    else:
        # or just create a new one (with default values pre-set)...
        model = ModelClass()
#        model.initialize()

    if request.method == 'POST':
        form = FormClass(request.POST,instance=model,request=request)
        if form.is_valid():
            print "valid!"
            model = form.save(commit=False)
            model.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse('django_cim_forms.views.detail', args=(app_name,model_name,model.id)))
        else:
            print "invalid!"


    else:
        # if this the the first time I'm loading this model, then initialize=True
        form = FormClass(instance=model,request=request,initialize=not(model.id))

    return render_to_response('django_cim_forms/metadata_detail.html', {'form' : form, "id" : model.id}, context_instance=RequestContext(request))


#################################################################
# create a form showing available field values                  #
# (lets users choose which models to add to relationship fields #
#################################################################

def lil_form_factory(model_to_render,fields_to_render):
    # this works with a list of fields
    # in theory, I only need one, but this can handle many in case I need it in the future
    class _form(ModelForm):
        class Meta:
            model = model_to_render
            fields = fields_to_render
            widgets = dict((fieldName,Select()) for fieldName in fields_to_render)
    return _form

def get_lil_form(request):
    app = request.GET.get('a', None)
    model = request.GET.get('m', None)
    fields = request.GET.get('f', None)
    ids_to_exclude = request.GET.get('i',"")
    if not app or not model or not fields:
        msg = "invalid or incomplete app/model/field combination"
        return HttpResponseBadRequest(msg)

    ids_to_exclude = [int(id) for id in ids_to_exclude.split(",") if id and id != "None"]

    model_type  = ContentType.objects.get(app_label=app.lower(),model=model.lower())
    model_class = model_type.model_class()
    form = lil_form_factory(model_class,[fields])()

    # TODO: in theory, this ought to be made to work w/ lists of fields
    qs = form.fields[fields].queryset.exclude(pk__in=ids_to_exclude)
    form.fields[fields].queryset = qs

    formTemplate = Template("<p>existing models:</p>{%for field in form.visible_fields %} {{ field }} {% endfor %}")
    formContext  = Context({"form" : form})

    return HttpResponse(formTemplate.render(formContext));

def get_lil_content(request):
    app_to_get = request.GET.get('a', None)
    model_to_get = request.GET.get('m', None)
    id_to_get = request.GET.get('i',"")
    if not app_to_get or not model_to_get or not id_to_get:
        return HttpResponseBadRequest("invalid or incomplete app/model/id combination")

    model_type  = ContentType.objects.get(app_label=app_to_get.lower(),model=model_to_get.lower())
    model = model_type.get_object_for_this_type(pk=id_to_get)
    json_data = model.serialize(format="json")
    return HttpResponse(json_data);
    #model_class = model_type.model_class()
    #form  = model_class.getForm(instance=model)
    #formTemplate = Template("{{ form.initial }}")
    #formContext  = Context({"form" : form})
    #return HttpResponse(formTemplate.render(formContext));
