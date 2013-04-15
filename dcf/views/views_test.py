
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
__date__ ="Feb 1, 2013 4:33:04 PM"

"""
.. module:: views_test

Summary of module goes here

"""

from django.template import *
from django.shortcuts import *
from django.http import *

from django.forms import *
from django.forms.models import BaseForm, BaseFormSet, BaseInlineFormSet, BaseModelFormSet, formset_factory, inlineformset_factory, modelform_factory, modelformset_factory
from django.forms.models import model_to_dict
from django.core.exceptions import ObjectDoesNotExist, FieldError, MultipleObjectsReturned

from django.utils import simplejson as json

from dcf.utils import *
from dcf.models import *

def TestFormSetFactory(model_class,*args,**kwargs):
    _form = modelformset_factory(model_class,*args,**kwargs)
    return _form

def test_bak(request,version_name="",project_name="",model_name=""):

#    categorization = MetadataCategorization.objects.get(pk=1)
#    print categorization
#
#    newCategory = MetadataAttributeCategory()
#    print newCategory.getGUID()
#    newCategory.save()
#    newCategory = MetadataPropertyCategory()
#    print newCategory.getGUID()
#    newCategory.save()
#    newCategory = MetadataPropertyCategory()
#    print newCategory.getGUID()
#    newCategory.save()
#    attributeCategories = MetadataAttributeCategory.objects.all()
#    print attributeCategories
#
#    propertyCategories = MetadataPropertyCategory.objects.all()
#    print propertyCategories
#
#    print "BEFORE: %s" % categorization.getCategories()
#    categorization.addCategories(attributeCategories)
#    print "ADDED ATTRIBUTES %s" % categorization.getCategories()
#    categorization.addCategory(propertyCategories[0])
#    print "ADDED PROPERTY %s" % categorization.getCategories()
#
#    print "JUST GET ONE: %s" % categorization.getPropertyCategories()
#

#    template = loader.get_template("dcf/glisaclimate.html")
#    context = RequestContext(request,{})
#    response = HttpResponse(template.render(context))
#    return response

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

    if len(filterParameters)>0:
        # a _specific_ model may have been requested
        try:
            model = TestModel.objects.get(**filterParameters)
        except FieldError,TypeError:
            # raise an error if some of the filter parameters were invalid
            msg = "Unable to create a TestModel with the following parameters: %s" % (", ").join([u'%s=%s'%(key,value) for (key,value) in filterParameters.iteritems()])
            return dcf_error(request,msg)
        except MultipleObjectsReturned:
            # raise an error if those filter params weren't enough to uniquely identify a customizer
            msg = "Unable to find a <i>single</i> TestModel with the following parameters: %s" % (", ").join([u'%s=%s'%(key,value) for (key,value) in filterParameters.iteritems()])
            return dcf_error(request,msg)
        except TestModel.DoesNotExist:
            # if there is nothing w/ those filter params, then create a new customizer
            # (note, it won't be saved until the user submits the form)
            model = TestModel(**filterParameters)
    else:
        # otherwise, just return a new customizer
        model = TestModel(**filterParameters)

    class _TestForm(ModelForm):
        class Meta:
            model = TestModel

        def __init__(self,*args,**kwargs):
            super(_TestForm,self).__init__(*args,**kwargs)
            model = self.instance
            
###
###            print "INIT FORM: %s" % model.getGUID()
###
###            submodel_qs = TestSubModel.objects.filter(parentGUID=model.getGUID())
###            self.fields["subModels"].queryset = submodel_qs
###            #self.fields["subModels"].initial = [subModel.pk for subModel in submodel_qs]
###            self.initial = {"subModels" : [subModel.pk for subModel in submodel_qs]}

###        def clean(self):
###            model = self.instance
###            cleaned_data = self.cleaned_data
###            print [subModel.pk for subModel in model.getSubModels()]
###            for subModel in model.getSubModels():
###                subModel.save()
###            print [subModel.pk for subModel in model.getSubModels()]
###            cleaned_data["subModel"] = [subModel.pk for subModel in model.getSubModels()]
###
###            return cleaned_data

    if request.method == "POST":

        form = _TestForm(request.POST,instance=model)
        print "one"
        if form.is_valid():
            print "two"
            model = form.save(commit=False)
            print "three"
            model.save()
            print "four"
            form.save_m2m()
            print "five"
        else:
            print form.errors

    else:
        form = _TestForm(instance=model)

    

    if model.pk:
        print "OLD MODEL, SUBMODELS ARE: %s" % model.subModels.all()
        TestFormSet = TestFormSetFactory(TestSubModel,extra=0)
        formset = TestFormSet(queryset=TestSubModel.objects.filter(parent=model))
    else:
        print "NEW MODEL, SUBMODELS ARE: %s" % model.tmpSubModels

        initial = [model_to_dict(subModel) for subModel in model.tmpSubModels]
        TestFormSet = TestFormSetFactory(TestSubModel,extra=len(initial))
        formset = TestFormSet(queryset=TestSubModel.objects.none(),initial=initial)#,extra=len(initial))



    dict = {}
    dict["form"] = form
    dict["formset"] = formset#TestFormSet(queryset=TestSubModel.objects.filter(parent=model))
    return render_to_response('dcf/test.html', dict, context_instance=RequestContext(request))


def test(request,model_id=""):

    msg = ""

    if model_id:
        model = MetadataTest.objects.get(pk=model_id)
    else:
        model = MetadataTest()
    FormClass = modelform_factory(MetadataTest)

    if request.method == "POST":
        form = FormClass(request.POST,instance=model)
        if form.is_valid():
            model = form.save(commit=False)
            model.save()
            form.save_m2m()
    else:
        form = FormClass(instance=model)

    dict = {}
    dict["STATIC_URL"]  = "/static/"
    dict["msg"]         = msg
    dict["form"]        = form
    dict["parent_id"]   = model.pk or ""

    return render_to_response('dcf/test.html', dict, context_instance=RequestContext(request))


def test2(request,model_id=""):

    msg = ""

    if model_id:
        model = MetadataTest.objects.get(pk=model_id)
        submodel = model.subModel
    else:
        model = MetadataTest()
        submodel = model.subModel

    if not submodel:
        submodel = MetadataTest()

    FormClass = modelform_factory(MetadataTest)

    if request.method == "POST":
        form = FormClass(request.POST,instance=submodel)
        if form.is_valid():
            submodel = form.save(commit=False)
            submodel.save()
            form.save_m2m()

            # outputting JSON w/ pk & name to add as option to formfield
            json_submodel = json.dumps({"pk":submodel.pk,"unicode":u'%s'%submodel})
            return HttpResponse(json_submodel,mimetype='application/json')
        else:
            msg = "Unable to save.  Please review the form and try again."

    else:
        form = FormClass(instance=submodel)
    
    dict = {}
    dict["STATIC_URL"]  = "/static/"
    dict["msg"]         = msg
    dict["form"]        = form
    dict["parent_id"]   = submodel.pk or ""

    rendered_form = django.template.loader.render_to_string("dcf/test2.html", dictionary=dict, context_instance=RequestContext(request))
    return HttpResponse(rendered_form)


