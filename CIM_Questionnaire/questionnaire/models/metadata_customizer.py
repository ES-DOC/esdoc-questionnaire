
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
__date__ ="Dec 27, 2013 10:30:35 AM"

"""
.. module:: questionnaire_customizer

Summary of module goes here

"""

from django.db import models
from django.db.models.fields import FieldDoesNotExist
#from django.utils.functional import lazy

from django.template.defaultfilters import slugify

from collections import OrderedDict
from django.utils import timezone

from CIM_Questionnaire.questionnaire.models.metadata_vocabulary import MetadataVocabulary

from CIM_Questionnaire.questionnaire.fields import MetadataFieldTypes, MetadataAtomicFieldTypes, EnumerationField, CardinalityField, MetadataUnitTypes
from CIM_Questionnaire.questionnaire.utils import LIL_STRING, SMALL_STRING, BIG_STRING, HUGE_STRING, QuestionnaireError
from CIM_Questionnaire.questionnaire.utils import find_in_sequence, validate_no_spaces, validate_no_reserved_words, valiate_no_bad_chars

from CIM_Questionnaire.questionnaire import APP_LABEL

class MetadataCustomizer(models.Model):
    class Meta:
        app_label   = APP_LABEL
        abstract    = True

    created                 = models.DateTimeField(blank=True,null=True,editable=False)
    last_modified           = models.DateTimeField(blank=True,null=True,editable=False)

    def refresh(self):
        """re-gets the model from the db"""
        if not self.pk:
            return self
        return self.__class__.objects.get(pk=self.pk)

    def save(self,*args,**kwargs):
        if not self.id:
            #self.created = datetime.datetime.today()
            self.created = timezone.now()
        #self.last_modified = datetime.datetime.now()
        self.last_modified = timezone.now()
        super(MetadataCustomizer,self).save(*args,**kwargs)

    @classmethod
    def get_new_customizer_set(cls,project,version,model_proxy,vocabularies):
        """creates the full set of (default) customizations required for a particular project/version/proxy combination w/ a specified list of vocabs"""

        # setup the model customizer...
        model_customizer = MetadataModelCustomizer(
            project=project,
            version=version,
            proxy=model_proxy,
            # vocabularies=vocabularies,
            vocabulary_order=",".join(map(str,[vocabulary.pk for vocabulary in vocabularies])),
        )
        model_customizer.reset()

        # setup the standard category customizers...
        standard_category_customizers = [
            MetadataStandardCategoryCustomizer(
                model_customizer=model_customizer,
                proxy=standard_category_proxy,
            )
            for standard_category_proxy in version.categorization.categories.all()
        ]
        for standard_category_customizer in standard_category_customizers:
            standard_category_customizer.reset()

        # setup the standard property customizers...
        standard_property_customizers = [
            MetadataStandardPropertyCustomizer(
                model_customizer=model_customizer,
                proxy=standard_property_proxy,
                category=find_in_sequence(lambda category: category.proxy.has_property(standard_property_proxy),standard_category_customizers),
                reset=True,
            )
            for standard_property_proxy in model_proxy.standard_properties.all()
        ]

        # setup the scientific category & property customizers
        scientific_category_customizers = {}
        scientific_property_customizers = {}
        for vocabulary in vocabularies:
            vocabulary_key = slugify(vocabulary.name)
            scientific_category_customizers[vocabulary_key] = {}
            scientific_property_customizers[vocabulary_key] = {}
            for component in vocabulary.component_proxies.all():
                component_key = slugify(component.name)
                model_key = u"%s_%s" % (vocabulary_key,component_key)
                scientific_category_customizers[vocabulary_key][component_key] = []
                scientific_property_customizers[vocabulary_key][component_key] = []
                for scientific_property_proxy in component.scientific_properties.all():
                    scientific_category_proxy = scientific_property_proxy.category
                    if scientific_category_proxy:
                        scientific_category_key = scientific_category_proxy.key
                        if scientific_category_key in [scientific_category.key for scientific_category in scientific_category_customizers[vocabulary_key][component_key]]:
                            scientific_category_customizer = find_category_by_key(scientific_category_key,scientific_category_customizers[vocabulary_key][component_key])
                        else:
                            scientific_category_customizer = MetadataScientificCategoryCustomizer(
                                model_customizer=model_customizer,
                                proxy=scientific_category_proxy,
                                vocabulary_key=vocabulary_key,
                                component_key=component_key,
                                model_key=model_key
                            )
                            scientific_category_customizer.reset()
                            scientific_category_customizers[vocabulary_key][component_key].append(scientific_category_customizer)
                    else:
                        scientific_category_customizer = None

                    scientific_property_customizer = MetadataScientificPropertyCustomizer(
                        model_customizer    = model_customizer,
                        proxy               = scientific_property_proxy,
                        vocabulary_key      = vocabulary_key,
                        component_key       = component_key,
                        model_key           = model_key,
                        category            = scientific_category_customizer,
                        reset               = True,
                    )
                    scientific_property_customizers[vocabulary_key][component_key].append(scientific_property_customizer)

        return (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers)

    @classmethod
    def get_existing_customizer_set(cls,model_customizer,vocabularies):
        """retrieves the full set of customizations used by a particular model_customizer w/ a specified list of vocabs"""

        standard_category_customizers = model_customizer.standard_property_category_customizers.all()
        standard_property_customizers = model_customizer.standard_property_customizers.all().order_by("category__order","order")

        # don't get _all_ of the scientific customizers
        # just get the ones associated w/ the vocabularies that were passed in
        # (see below)
        #
        # scientific_category_customizers = {}
        # for scientific_category_customizer in model_customizer.scientific_property_category_customizers.all():
        #     vocabulary_key = scientific_category_customizer.vocabulary_key
        #     component_key = scientific_category_customizer.component_key
        #     if not vocabulary_key in scientific_category_customizers:
        #         scientific_category_customizers[vocabulary_key] = {}
        #     if not component_key in scientific_category_customizers[vocabulary_key]:
        #         scientific_category_customizers[vocabulary_key][component_key] = []
        #     scientific_category_customizers[vocabulary_key][component_key].append(scientific_category_customizer)
        #
        # scientific_property_customizers = {}
        # for scientific_property_customizer in model_customizer.scientific_property_customizers.all():
        #     vocabulary_key = scientific_property_customizer.vocabulary_key
        #     component_key = scientific_property_customizer.component_key
        #     if not vocabulary_key in scientific_property_customizers:
        #         scientific_property_customizers[vocabulary_key] = {}
        #     if not component_key in scientific_property_customizers[vocabulary_key]:
        #         scientific_property_customizers[vocabulary_key][component_key] = []
        #     scientific_property_customizers[vocabulary_key][component_key].append(scientific_property_customizer)

        scientific_category_customizers = {}
        scientific_property_customizers = {}
        for vocabulary in vocabularies:
            vocabulary_key = slugify(vocabulary.name)
            scientific_category_customizers[vocabulary_key] = {}
            scientific_property_customizers[vocabulary_key] = {}
            for component in vocabulary.component_proxies.all():
                component_key = slugify(component.name)
                scientific_category_customizers[vocabulary_key][component_key] = model_customizer.scientific_property_category_customizers.filter(vocabulary_key=vocabulary_key,component_key=component_key)
                scientific_property_customizers[vocabulary_key][component_key] = model_customizer.scientific_property_customizers.filter(vocabulary_key=vocabulary_key,component_key=component_key).order_by("category__order","order")

        return (model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers)

    @classmethod
    def save_customizer_set(cls,model_customizer,standard_category_customizers,standard_property_customizers,scientific_category_customizers,scientific_property_customizers):

        model_customizer.save()

        # this fn is called outside of the forms, so I have to manually re-create and add the m2m field here
        vocabularies = MetadataVocabulary.objects.filter(pk__in=model_customizer.vocabulary_order)
        model_customizer.vocabularies = vocabularies
        model_customizer.save()

        for standard_category_customizer in standard_category_customizers:
            standard_category_customizer.model_customizer = model_customizer
            standard_category_customizer.save()

        for standard_property_customizer in standard_property_customizers:
            category_customizer_key = slugify(standard_property_customizer.category_name)
            category = find_in_sequence(lambda category_customizer: category_customizer.key==category_customizer_key,standard_category_customizers)
            standard_property_customizer.category = category
            standard_property_customizer.model_customizer = model_customizer
            standard_property_customizer.save()

        for vocabulary_key,scientific_category_customizer_dict in scientific_category_customizers.iteritems():
            for component_key,scientific_category_customizer_list in scientific_category_customizer_dict.iteritems():
                for scientific_category_customizer in scientific_category_customizer_list:
                    scientific_category_customizer.model_customizer = model_customizer
                    scientific_category_customizer.save()

        for vocabulary_key,scientific_property_customizer_dict in scientific_property_customizers.iteritems():
            for component_key,scientific_property_customizer_list in scientific_property_customizer_dict.iteritems():
                for scientific_property_customizer in scientific_property_customizer_list:
                    category_customizer_key = slugify(scientific_property_customizer.category_name)
                    category = find_in_sequence(lambda category_customizer: category_customizer.key==category_customizer_key,scientific_category_customizers[vocabulary_key][component_key])
                    scientific_property_customizer.category = category
                    scientific_property_customizer.model_customizer = model_customizer
                    scientific_property_customizer.save()

    def get_unique_together(self):
        # This fn is required because 'unique_together' validation is only enforced at the modelform
        # if all unique_together fields appear in the modelform; If not, I have to manually validate
        unique_together = self._meta.unique_together
        return list(unique_together)

    def get_field(self,field_name):
        try:
            field = self._meta.get_field_by_name(field_name)
        except FieldDoesNotExist:
            msg = "Could not find a field called '%s'" % (field_name)
            #raise QuestionnaireError(msg)
            return None
        return field[0]

    @classmethod
    def get_field(cls,field_name):
        try:
            field = cls._meta.get_field_by_name(field_name)
        except FieldDoesNotExist:
            msg = "Could not find a field called '%s'" % (field_name)
            #raise QuestionnaireError(msg)
            return None
        return field[0]

class MetadataModelCustomizer(MetadataCustomizer):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False

        unique_together = ("name","project","version","proxy") # proxy defines the actual model

        # TODO: DELETE THESE NEXT TWO LINES
        verbose_name        = '(DISABLE ADMIN ACCESS SOON) Metadata Model Customizer'
        verbose_name_plural = '(DISABLE ADMIN ACCESS SOON) Metadata Model Customizers'

    proxy                   = models.ForeignKey("MetadataModelProxy",blank=True,null=True)

    project                 = models.ForeignKey("MetadataProject",blank=True,null=True,related_name="model_customizers")
    version                 = models.ForeignKey("MetadataVersion",blank=True,null=True,related_name="model_customizers")
    vocabularies            = models.ManyToManyField("MetadataVocabulary",blank=True,null=True) # cannot set 'limit_choices_to' here, instead setting 'queryset' on form
    vocabularies.help_text  = "Choose which Controlled Vocabularies (in which order) apply to this model."
    vocabulary_order        = models.CommaSeparatedIntegerField(max_length=BIG_STRING,blank=True,null=True)

    name                    = models.CharField(max_length=SMALL_STRING,blank=False,null=False)
    name.help_text          = "A unique name for this customization (ie: \"basic\" or \"advanced\")"
    description             = models.TextField(verbose_name="Customization Description",blank=True,null=True)
    description.help_text   = "An explanation of how this customization is intended to be used.  This information is for informational purposes only."
    default                 = models.BooleanField(verbose_name="Is Default Customization",blank=True,default=False)
    default.help_text       = "Defines the default customization that is used by this project/model combination if no explicit customization is provided."

    model_title                         = models.CharField(max_length=BIG_STRING,verbose_name="Name that should appear on the Document Form",blank=False,null=True)
    model_description                   = models.TextField(verbose_name="A description of the document",blank=True,null=True)
    model_description.help_text         = "This text will appear as documentation in the editing form.  Inline HTML formatting is permitted."
    model_show_all_categories           = models.BooleanField(verbose_name="Display empty categories",default=False)
    model_show_all_categories.help_text = "Include categories in the editing form for which there are no (visible) attributes associated with"
    model_show_all_properties           = models.BooleanField(verbose_name="Display uncategorized fields",default=True)
    model_show_all_properties.help_text = "Include attributes in the editing form that have no associated category.  These will show up below any category tabs."
    model_show_hierarchy                = models.BooleanField(verbose_name="Include the full component hierarchy",default=True)
    model_show_hierarchy.help_text      ="Some CIM SoftwareComponents are comprised of a hierarchy of nested child components.  Checking this option allows that full hierarchy to be edited at once in the CIM Editor."
    model_hierarchy_name                = models.CharField(max_length=LIL_STRING,verbose_name="Title of the component hierarchy tree",default="Component Hierarchy")
    model_hierarchy_name.help_text      = "What should the title be for widget that navigates the component hierarchy?"
    model_root_component                = models.CharField(max_length=LIL_STRING,verbose_name="Name of the root component",blank=True,validators=[validate_no_spaces],default="RootComponent")
    model_root_component.help_text      = "If this component uses mulitple CVs, then the corresponding component hierarchies will be grouped under a single root component.  Please provide the component name here."


    def __unicode__(self):
    #    return u'%s::%s::%s' % (self.project,self.proxy,self.name)
        return u'%s' % (self.name)

    def reset(self):
        proxy = self.proxy

        if not proxy:
            msg = "Trying to reset a customizer w/out a proxy having been specified."
            raise QuestionnaireError(msg)

        self.model_title                = proxy.name
        self.model_description          = proxy.documentation

        self.model_show_all_categories  = self.get_field("model_show_all_categories").default
        self.model_show_all_properties  = self.get_field("model_show_all_properties").default
        self.model_show_hierarchy       = self.get_field("model_show_hierarchy").default
        self.model_hierarchy_name       = self.get_field("model_hierarchy_name").default
        self.model_root_component       = self.get_field("model_root_component").default

    def clean(self):
        # force name to be lowercase
        # this avoids hacky methods of ensuring case-insensitive uniqueness
        self.name = self.name.lower()

    def save(self,*args,**kwargs):
        # only one customizer can be default at a time
        # (this is handled via a ValidationError in the form,
        # however, I still do the check here in-case I'm manipulating customizers outside of the form)
        if self.default:
            other_customizer_filter_kwargs = {
                "default"   : True,
                "proxy"     : self.proxy,
                "project"   : self.project,
                "version"   : self.version,
            }
            other_default_customizers = MetadataModelCustomizer.objects.filter(**other_customizer_filter_kwargs)
            if self.pk:
                other_default_customizers.exclude(pk=self.pk)
            if other_default_customizers.count() != 0:
                other_default_customizers.update(default=False)

        super(MetadataModelCustomizer,self).save(*args,**kwargs)

    def get_active_standard_categories(self):
        if self.model_show_all_categories:
            return self.standard_property_category_customizers.all()
        else:
            # exclude categories for which there are no corresponding properties
            #return self.standard_property_category_customizers.all().exclude(standard_property_customizers__isnull=True)#.exclude(standard_property_customizers__isnull=True)
            return self.standard_property_category_customizers.filter(standard_property_customizers__displayed=True).distinct()

    def get_active_standard_properties(self):
        if self.model_show_all_properties:
            return self.standard_property_customizers.filter(displayed=True)
        else:
            self.standard_property_customizers.filter(displayed=True,category__isnull=False)

    def get_active_standard_properties_for_category(self,category):
        return self.standard_property_customizers.filter(displayed=True,category=category)

    def get_active_standard_categories_and_properties(self):
        categories_and_properties = OrderedDict()
        for category in self.get_active_standard_categories():
            categories_and_properties[category] = self.get_active_standard_properties_for_category(category)
        # this makes sure the results are sorted by category.order
        # though it's not actually needed b/c I'm explicitly using an OrderedDict above
        #return sorted(categories_and_properties.iteritems(),key=lambda category_and_properties_pair: category_and_properties_pair[0].order)
        return categories_and_properties

    def get_active_scientific_categories_by_key(self,model_key):
        if self.model_show_all_categories:            
            return self.scientific_property_category_customizers.filter(model_key=model_key)
        else:
            return self.scientific_property_category_customizers.filter(model_key=model_key).filter(scientific_property_customizers__displayed=True).distinct()

    def get_active_scientific_properties_by_key(self,model_key):
        if self.model_show_all_properties:
            return self.scientific_property_customizers.filter(model_key=model_key,displayed=True)
        else:
            self.scientific_property_customizers.filter(model_key=model_key,displayed=True,category__isnull=False)

    def get_active_scientific_properties_for_category(self,category):
        return self.scientific_property_customizers.filter(displayed=True,category=category)

    def get_active_scientific_categories_and_properties_by_key(self,model_key):
        categories_and_properties = OrderedDict()
        for category in self.get_active_scientific_categories_by_key(model_key):
            categories_and_properties[category] = self.get_active_scientific_properties_for_category(category)
        # this makes sure the results are sorted by category.order
        # though it's not actually needed b/c I'm explicitly using an OrderedDict above
        #return sorted(categories_and_properties.iteritems(),key=lambda category_and_properties_pair: category_and_properties_pair[0].order)
        return categories_and_properties

def find_category_by_key(key,sequence):
    for category in sequence:
        if category.key == key:
            return category
    return None

class MetadataCategoryCustomizer(MetadataCustomizer):
    class Meta:
        app_label   = APP_LABEL
        abstract    = True

    pending_deletion        = models.BooleanField(blank=False,default=False)

class MetadataStandardCategoryCustomizer(MetadataCategoryCustomizer):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False

        # TODO: DELETE THESE NEXT TWO LINES
        verbose_name        = '(DISABLE ADMIN ACCESS SOON) Metadata Standard Category Customizer'
        verbose_name_plural = '(DISABLE ADMIN ACCESS SOON) Metadata Standard Category Customizers'

        ordering        = ['order']
        unique_together = ("name","project","proxy","model_customizer")

    model_customizer        = models.ForeignKey("MetadataModelCustomizer",blank=True,null=True,related_name="standard_property_category_customizers")

    proxy                   = models.ForeignKey("MetadataStandardCategoryProxy",blank=True,null=True)

    project                 = models.ForeignKey("MetadataProject",blank=True,null=True,related_name="model_standard_category_customizers")
    version                 = models.ForeignKey("MetadataVersion",blank=True,null=True,related_name="model_standard_category_customizers")

    name                    = models.CharField(max_length=BIG_STRING,blank=False,null=False)
    key                     = models.CharField(max_length=BIG_STRING,blank=True,null=True)
    description             = models.TextField(blank=True,null=True)
    order                   = models.PositiveIntegerField(blank=True,null=True)
    order.help_text = "Drag and drop the corresponding category widget to modify its order."


    def __unicode__(self):
        #return u'%s::%s' % (self.project,self.proxy)
        return u'%s' % (self.name)

    def __init__(self,*args,**kwargs):
        super(MetadataStandardCategoryCustomizer,self).__init__(*args,**kwargs)
        if not self.project:
            if self.model_customizer:   # put this check in for the ajax_customize_category fn
                self.project = self.model_customizer.project
        if not self.version:
            if self.model_customizer:   # put this check in for the ajax_customize_category fn
                self.version = self.model_customizer.version
        
    def reset(self):
        proxy = self.proxy

        if not proxy:
            msg = "Trying to reset a MetadataStandardCategoryCustomizer w/out a proxy having been specified."
            raise QuestionnaireError(msg)

        self.name               = proxy.name
        self.key                = proxy.key
        self.description        = proxy.description
        self.order              = proxy.order
        self.pending_deletion   = False

class MetadataScientificCategoryCustomizer(MetadataCategoryCustomizer):
    class Meta:
        app_label   = APP_LABEL
        abstract    = False

        # TODO: DELETE THESE NEXT TWO LINES
        verbose_name        = '(DISABLE ADMIN ACCESS SOON) Metadata Scientific Category Customizer'
        verbose_name_plural = '(DISABLE ADMIN ACCESS SOON) Metadata Scientific Category Customizers'

        ordering        = ['order']
        unique_together = ("name","project","proxy","vocabulary_key","component_key","model_customizer")

    model_customizer        = models.ForeignKey("MetadataModelCustomizer",blank=True,null=True,related_name="scientific_property_category_customizers")

    proxy                   = models.ForeignKey("MetadataScientificCategoryProxy",blank=True,null=True)

    project                 = models.ForeignKey("MetadataProject",blank=True,null=True,related_name="model_scientific_category_customizers")
    vocabulary_key          = models.CharField(blank=True,null=True,max_length=BIG_STRING)
    component_key           = models.CharField(blank=True,null=True,max_length=BIG_STRING)
    model_key               = models.CharField(blank=True,null=True,max_length=BIG_STRING)

    name                    = models.CharField(max_length=BIG_STRING,blank=False,null=False)
    key                     = models.CharField(max_length=BIG_STRING,blank=True,null=True)
    description             = models.TextField(blank=True,null=True)
    order                   = models.PositiveIntegerField(blank=True,null=True)
    order.help_text = "Drag and drop the corresponding category widget to modify its order."


    def __unicode__(self):
        #return u'%s::%s' % (self.project,self.proxy)
        return u'%s'%(self.name)

    def __init__(self,*args,**kwargs):
        super(MetadataScientificCategoryCustomizer,self).__init__(*args,**kwargs)
        self.model_key = u"%s_%s"%(self.vocabulary_key,self.component_key)
        if not self.project:
            if self.model_customizer:   # put this check in for the ajax_customize_category fn
                self.project = self.model_customizer.project
                
    def save(self,*args,**kwargs):
        self.model_key = u"%s_%s"%(self.vocabulary_key,self.component_key)
        super(MetadataScientificCategoryCustomizer,self).save(*args,**kwargs)

    def reset(self,reset_keys=False):
        proxy = self.proxy
        if not self.proxy:
            msg = "Trying to reset a MetadataScientificCategoryCustomizer w/out a proxy having been specified."
            raise QuestionnaireError(msg)

        if proxy:
            self.name               = proxy.name
            self.description        = proxy.description
            self.key                = proxy.key
            self.order              = proxy.order

            if reset_keys:
                component = proxy.component
                component_key  = slugify(component.name)
                vocabulary_key = slugify(component.vocabulary.name)
                self.vocabulary_key     = vocabulary_key
                self.component_key      = component_key
                self.model_key          = "%s_%s"%(vocabulary_key,component_key)

        self.pending_deletion   = False



class MetadataPropertyCustomizer(MetadataCustomizer):
    class Meta:
        app_label   = APP_LABEL
        abstract    = True
        ordering    = ['order'] # don't think this is doing anything since class is abstract
                                # the concrete child classes repeat this line to ensure order is kept

    name        = models.CharField(max_length=SMALL_STRING,blank=False,null=False)
    order       = models.PositiveIntegerField(blank=True,null=True)
    field_type  = models.CharField(max_length=64,blank=True,choices=[(ft.getType(),ft.getName()) for ft in MetadataFieldTypes])

    # ways to customize _any_ field...
    displayed           = models.BooleanField(default=True,blank=True,verbose_name="should this property be displayed?")
    required            = models.BooleanField(default=True,blank=True,verbose_name="is this property required?")
    editable            = models.BooleanField(default=True,blank=True,verbose_name="can the value of this property be edited?")
    unique              = models.BooleanField(default=False,blank=True,verbose_name="must the value of this property be unique?")
    verbose_name        = models.CharField(max_length=64,blank=False,verbose_name="how should this property be labeled (overrides default name)?")
    default_value       = models.CharField(max_length=128,blank=True,null=True,verbose_name="what is the default value of this property?")
    documentation       = models.TextField(blank=True,verbose_name="what is the help text to associate with property?")
    inline_help         = models.BooleanField(default=False,blank=True,verbose_name="should the help text be displayed inline?")
    
    
class MetadataStandardPropertyCustomizer(MetadataPropertyCustomizer):
    class Meta:
        app_label    = APP_LABEL
        abstract     = False
        ordering     = ['order']

        # TODO: DELETE THESE NEXT TWO LINES
        verbose_name        = '(DISABLE ADMIN ACCESS SOON) Metadata Standard Property Customizer'
        verbose_name_plural = '(DISABLE ADMIN ACCESS SOON) Metadata Standard Property Customizers'

    proxy            = models.ForeignKey("MetadataStandardPropertyProxy",blank=True,null=True)
    model_customizer = models.ForeignKey("MetadataModelCustomizer",blank=False,null=True,related_name="standard_property_customizers")

    category         = models.ForeignKey("MetadataStandardCategoryCustomizer",blank=True,null=True,related_name="standard_property_customizers")
    category_name    = models.CharField(blank=True,null=True,max_length=BIG_STRING)

    inherited           = models.BooleanField(default=False,blank=True,verbose_name="can this property be inherited by children?")
    inherited.help_text = "Enabling inheritance will allow the correponding properties of child components to 'inherit' the value of this property.  The editing form will allow users the ability to 'opt-out' of this inheritance."

    # ways to customize an atomic field
    atomic_type           = models.CharField(max_length=BIG_STRING,blank=True,verbose_name="how should this field be rendered?",
        choices=[(ft.getType(),ft.getName()) for ft in MetadataAtomicFieldTypes],
        default=MetadataAtomicFieldTypes.DEFAULT.getType(),
    )
    atomic_type.help_text = "By default, all fields are rendered as strings.  However, a field can be customized to accept longer snippets of text, dates, email addresses, etc."
    suggestions           = models.TextField(blank=True,verbose_name="are there any suggestions you would like to offer to users?")
    suggestions.help_text = "Please enter a \"|\" separated list.  These suggestions will only take effect for text fields, in the case of Standard Properties, or for text fields or when \"OTHER\" is selected, in the case of Scientific Properties.  They appear as an auto-complete widget and not as a formal enumeration."

    # ways to customize an enumeration field
    enumeration_choices  = EnumerationField(blank=True,null=True,verbose_name="choose the property values that should be presented to users.")
    enumeration_default  = EnumerationField(blank=True,null=True,verbose_name="choose the default value(s), if any, for this property.")
    enumeration_open     = models.BooleanField(default=False,blank=True,verbose_name="check if a user can specify a custom property value.")
    enumeration_multi    = models.BooleanField(default=False,blank=True,verbose_name="check if a user can specify multiple property values.")
    enumeration_nullable = models.BooleanField(default=False,blank=True,verbose_name="check if a user can specify an explicit \"NONE\" value.")

    # ways to customize a relationship field
    relationship_cardinality   = CardinalityField(blank=True,verbose_name="how many instances (min/max) of this property are allowed?")
    relationship_show_subform  = models.BooleanField(default=False,blank=True,verbose_name="should this property be rendered in its own subform?")
    relationship_show_subform.help_text = "Checking this will cause the property to be rendered as a nested subform within the <i>parent</i> form; All properties of this model will be available to view and edit in that subform.\
                                          Unchecking it will cause the attribute to be rendered as a simple select widget.  This option is only available if the \"parent\" customizer has been saved."
    subform_customizer         = models.ForeignKey("MetadataModelCustomizer",blank=True,null=True,related_name="property_customizer")

    def __unicode__(self):
        return u'%s' % (self.proxy.name)

    def __init__(self,*args,**kwargs):

        reset = kwargs.pop("reset",False)

        super(MetadataStandardPropertyCustomizer,self).__init__(*args,**kwargs)

        proxy = self.proxy
        if reset:
            self.reset()

        # atomic fields...
        if self.field_type == MetadataFieldTypes.ATOMIC:
            pass

        # enumeration fields...
        elif self.field_type == MetadataFieldTypes.ENUMERATION:
            pass
            #enumeration_choices_field = self.get_field("enumeration_choices")
            #enumeration_choices_field.set_choices(proxy.enumeration_choices.split("|"))
            #enumeration_choices_field.set_enumeration(proxy.enumeration_choices.split("|"))

        # relationship fields...
        elif self.field_type == MetadataFieldTypes.RELATIONSHIP:
            pass

    def reset(self,reset_category=False):
        proxy = self.proxy

        if not proxy:
            msg = "Trying to reset a MetadataStandardPropertyCustomizer w/out a proxy having been specified."
            raise QuestionnaireError(msg)

        self.field_type     = proxy.field_type
        self.name           = proxy.name
        self.order          = proxy.order
        self.verbose_name   = proxy.name
        self.documentation  = proxy.documentation
        self.inline_help    = False

        # atomic fields...
        if self.field_type == MetadataFieldTypes.ATOMIC:
            self.atomic_type = proxy.atomic_type
        
        # enumeration fields...
        if self.field_type == MetadataFieldTypes.ENUMERATION:
# this has been moved to the __init__ fn above
#            enumeration_choices_field = self.get_field("enumeration_choices")
#            enumeration_choices_field.set_choices(proxy.enumeration_choices.split("|"))
            self.enumeration_choices = proxy.enumeration_choices

        # relationship fields...
        if self.field_type == MetadataFieldTypes.RELATIONSHIP:
            self.relationship_cardinality = proxy.relationship_cardinality.split("|")
            self.relationship_show_subform = False

        if self.category:
            self.category_name = self.category.name
            if reset_category:
                self.category.reset()
        
class MetadataScientificPropertyCustomizer(MetadataPropertyCustomizer):
    class Meta:
        app_label    = APP_LABEL
        abstract     = False
        ordering     = ['order']

        # TODO: DELETE THESE NEXT TWO LINES
        verbose_name        = '(DISABLE ADMIN ACCESS SOON) Metadata Scientific Property Customizer'
        verbose_name_plural = '(DISABLE ADMIN ACCESS SOON) Metadata Scientific Property Customizers'
        
    proxy            = models.ForeignKey("MetadataScientificPropertyProxy",blank=True,null=True)
    model_customizer = models.ForeignKey("MetadataModelCustomizer",blank=False,null=True,related_name="scientific_property_customizers")

    vocabulary_key   = models.CharField(blank=True,null=True,max_length=BIG_STRING)
    component_key    = models.CharField(blank=True,null=True,max_length=BIG_STRING)
    model_key        = models.CharField(blank=True,null=True,max_length=BIG_STRING)

    is_enumeration   = models.BooleanField(blank=False,default=False)
    
    category         = models.ForeignKey("MetadataScientificCategoryCustomizer",blank=True,null=True,related_name="scientific_property_customizers")
    category_name    = models.CharField(blank=True,null=True,max_length=BIG_STRING)

    atomic_type    = models.CharField(max_length=BIG_STRING,blank=True,verbose_name="how should this field be rendered?",
        choices=[(ft.getType(),ft.getName()) for ft in MetadataAtomicFieldTypes],
        default=MetadataAtomicFieldTypes.DEFAULT.getType(),
    )
    atomic_default = models.CharField(max_length=BIG_STRING,blank=True,null=True,verbose_name="what is the default value of this property?")

    enumeration_choices  = EnumerationField(blank=True,null=True,verbose_name="choose the property values that should be presented to users.")
    enumeration_default  = EnumerationField(blank=True,null=True,verbose_name="choose the default value(s), if any, for this property.")
    enumeration_open     = models.BooleanField(default=False,blank=True,verbose_name="check if a user can specify a custom property value.")
    enumeration_multi    = models.BooleanField(default=False,blank=True,verbose_name="check if a user can specify multiple property values.")
    enumeration_nullable = models.BooleanField(default=False,blank=True,verbose_name="check if a user can specify an explicit \"NONE\" value.")

    display_extra_standard_name = models.BooleanField(null=False,blank=False,default=False)
    display_extra_description   = models.BooleanField(null=False,blank=False,default=False)
    display_extra_units         = models.BooleanField(null=False,blank=False,default=False)
    edit_extra_standard_name    = models.BooleanField(null=False,blank=False,default=False)
    edit_extra_description      = models.BooleanField(null=False,blank=False,default=False)
    edit_extra_units            = models.BooleanField(null=False,blank=False,default=False)
    extra_standard_name         = models.CharField(blank=True,null=True,max_length=BIG_STRING)
    extra_description           = models.TextField(blank=True,null=True)
    extra_units                 = models.CharField(blank=True,null=True,max_length=BIG_STRING,choices=[(unit.getType(),unit.getName()) for unit in MetadataUnitTypes])

#    def __unicode__(self):
#        return u'%s::%s' % (self.model_customizer,self.proxy.name)

    def __init__(self,*args,**kwargs):

        reset = kwargs.pop("reset",False)

        super(MetadataScientificPropertyCustomizer,self).__init__(*args,**kwargs)

        proxy = self.proxy
        if reset:
            self.reset()

        # enumeration fields...
        if self.is_enumeration:
            #enumeration_choices_field = self.get_field("enumeration_choices")
            #enumeration_choices_field.set_enumeration(self.proxy.values.split("|"))
            #self._meta.get_field_by_name("enumeration_choices")[0]._choices = [(slugify(choice),choice) for choice in proxy.values.split("|")
            #    lazy(proxy.get_values_as_enumeration,list)()

            # TODO THE ERROR WAS THAT THIS IS OVERWRITING THE CHOICES FOR _ALL_ ENUMERATIONFIELDS IN THIS FORMSET
            pass

        # atomic fields...
        else:
            pass


    def reset(self,reset_category=False):

        proxy = self.proxy

        if not proxy:
            msg = "Trying to reset a MetadataScientificPropertyCustomizer w/out a proxy having been specified."
            raise QuestionnaireError(msg)

        if not self.model_key:
            self.model_key      = u"%s_%s" % (self.vocabulary_key,self.component_key)

        self.name           = proxy.name
        self.order          = proxy.order
        self.verbose_name   = proxy.name
        self.verbose_name   = proxy.name
        self.documentation  = proxy.documentation
        self.inline_help    = False
        self.field_type     = MetadataFieldTypes.PROPERTY.getType()

        self.display_extra_standard_name = False
        self.display_extra_description   = False
        self.display_extra_units         = False
        self.edit_extra_standard_name    = True
        self.edit_extra_description      = True
        self.edit_extra_units            = True


        if proxy.choice=="OR":
            self.is_enumeration = True
            self.enumeration_multi = True
            self.enumeration_open = False
            self.enumeration_nullable = False
            self.enumeration_choices = proxy.values
        elif proxy.choice=="XOR":
            self.is_enumeration = True
            self.enumeration_multi = False
            self.enumeration_open = False
            self.enumeration_nullable = False
            self.enumeration_choices = proxy.values
        elif proxy.choice=="keyboard":
            self.is_enumeration = False
        else:
            msg = "invalid choice specified: '%s'" % (proxy.choice)
            raise QuestionnaireError(msg)

        if self.category:
            self.category_name = self.category.name
            if reset_category:
                self.category.reset()

    def display_extra_attributes(self):
        display_extra_attributes = (self.display_extra_standard_name or self.display_extra_description or self.display_extra_units)
        return display_extra_attributes

    def enumerate_choices(self):
        return [(choice,choice) for choice in self.enumeration_choices.split("|")]