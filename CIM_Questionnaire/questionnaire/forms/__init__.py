__author__="allyn.treshansky"
__date__ ="$Dec 28, 2013 4:55:24 PM$"

from django.forms import *

from questionnaire.utils import *

class MetadataForm(ModelForm):


    customizer      = None
    cached_fields   = []
    current_values  = {}

    def get_customizer(self):
        return self.customizer

    def get_fields_from_list(self,field_list):
        return [field for field in self if field.name in field_list]

    def get_field_value_by_name(self,field_name):
        try:
            return self.current_values[field_name]
        except KeyError:
            msg = "Unable to locate field '%s' in form." % (field_name)
            raise QuestionnaireError(msg)
        
from forms_authentication   import  MetadataUserForm, MetadataPasswordForm, MetadataRegistrationForm, LocalAuthenticationForm, RemoteAuthenticationForm
from forms_customize        import  MetadataModelCustomizerForm, MetadataStandardPropertyCustomizerInlineFormSetFactory, MetadataScientificPropertyCustomizerInlineFormSetFactory
from forms_categorize       import  MetadataStandardCategoryCustomizerForm, MetadataScientificCategoryCustomizerForm
from forms_edit             import  MetadataModelFormSetFactory, MetadataStandardPropertyInlineFormSetFactory