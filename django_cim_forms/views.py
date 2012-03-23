# module imports.
from django.template import *
from django.shortcuts import *
from django.http import *

from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core import serializers

# intra/inter-package imports.

from django_cim_forms.models import *
from django_cim_forms.forms import *
from django_cim_forms.helpers import *


def index(request):
    return HttpResponse("this is the index page for the metadata application")

def detail(request, model_name, app_name="django_cim", model_id=None):
    
    # get the model & form...
    try:
        ModelType  = ContentType.objects.get(app_label=app_name,model=model_name.lower())
    except ObjectDoesNotExist:
        msg = "invalid model type '%s' in application '%s'" % (model_name, app_name)
        return HttpResponseBadRequest(msg)
    ModelClass = ModelType.model_class()
    FormClass  = getFormClassFromModelClass(ModelClass)

    print FormClass
    
    # sanity checks on the model & form...
    if not(ModelClass and issubclass(ModelClass,MetadataModel)):
        msg = "invalid model type: '%s'" % model_name
        return HttpResponseBadRequest(msg)
    if not(FormClass and issubclass(FormClass,MetadataForm)):
        msg = "cannot determine MetadataForm bound to model type: '%s'" % model_name
        return HttpResponseBadRequest(msg)


    if model_id:
        # try to load the specified model...
        model = get_object_or_404(ModelClass, pk=model_id)
    else:
        # or just create a new one...
        model = ModelClass()

    if request.method == 'POST':
        form = FormClass(request.POST,instance=model,request=request)
        if form.is_valid():
            print "valid!"
            model = form.save(commit=False)
            model.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse('metadata.views.detail', args=(app_name,model_name,model.id)))

    else:
        form = FormClass(instance=model,request=request)#,initial=model.initialize())

    return render_to_response('django_cim_forms/metadata_detail.html', {'form' : form, "id" : model.id}, context_instance=RequestContext(request))

def test(request):
    model = TestModel()
    form = TestForm()
    return render_to_response('django_cim_forms/test.html', {'form' : form},context_instance=RequestContext(request))
    return HttpResponse("this is the test page for the metadata application")
