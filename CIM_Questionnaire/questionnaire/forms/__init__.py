__author__="allyn.treshansky"
__date__ ="$Dec 28, 2013 4:55:24 PM$"

from django.forms import *

from questionnaire.utils import *


class MetadataForm(ModelForm):
    cached_fields   = []
  #  current_values  = {}

    def __init__(self,*args,**kwargs):
        super(MetadataForm,self).__init__(*args,**kwargs)

        # when initializing formsets,
        # the fields aren't always setup yet in the underlying model
        # so this gets them either from the request (in the case of POST) or initial (in the case of GET)

        self.current_values = {}
        
        if self.data:
            # POST; request was passed into constructor
            # (not sure why I can't do this in a list comprehension)
            for key,value in self.data.iteritems():
                if key.startswith(self.prefix+"-"):
                    self.current_values[key.split(self.prefix+"-")[1]] = value


        else:
            # GET; initial was passed into constructor
            self.current_values = self.initial

    def get_fields_from_list(self,field_list):
        return [field for field in self if field.name in field_list]

class MetadataCustomizerForm(MetadataForm):

#    current_values  = {}

    pass

class MetadataEditingForm(MetadataForm):

#    current_values  = {}

    customizer      = None

    def get_customizer(self):
        return self.customizer

    def get_field_value_by_name(self,field_name):
        try:
            return self.current_values[field_name]
        except KeyError:
            msg = "Unable to locate field '%s' in form." % (field_name)
            raise QuestionnaireError(msg)
        
from forms_authentication   import  MetadataUserForm, MetadataPasswordForm, MetadataRegistrationForm, LocalAuthenticationForm, RemoteAuthenticationForm
from forms_customize        import  MetadataModelCustomizerForm, MetadataStandardPropertyCustomizerInlineFormSetFactory, MetadataScientificPropertyCustomizerInlineFormSetFactory
from forms_categorize       import  MetadataStandardCategoryCustomizerForm, MetadataScientificCategoryCustomizerForm
from forms_edit             import  MetadataModelFormSetFactory, MetadataStandardPropertyInlineFormSetFactory, MetadataScientificPropertyInlineFormSetFactory