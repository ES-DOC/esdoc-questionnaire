__author__="allyn.treshansky"
__date__ ="$Dec 28, 2013 4:55:24 PM$"

from django.forms import *

from questionnaire.utils import *


class MetadataForm(ModelForm):

    cached_fields   = []

    ## these fields raise form validation errors with string Nones
    _fields_none_string_overload = ('id', 'enumeration_value', 'relationship_value')

    def __init__(self, *args, **kwargs):
        super(MetadataForm, self).__init__(*args, **kwargs)

        ## TODO: remove during form refactoring. this is hack to avoid "None" strings of uncertain origin.
        if self.data != {}:
            for k, v in self.data.iteritems():
                for f in self._fields_none_string_overload:
                    if k.endswith('-'+f) and v == 'None':
                        self.data[k] = None

#     def __init__(self,*args,**kwargs):
#         super(MetadataForm,self).__init__(*args,**kwargs)
#
# #        assert_no_string_nones(self.data)
#
#         # when initializing formsets,
#         # the fields aren't always setup yet in the underlying model
#         # so this gets them either from the request (in the case of POST) or initial (in the case of GET)
#
#         self.current_values = {}
#         
#         if self.data:
#             # POST; request was passed into constructor
#             for key,value in self.data.iteritems():
#                 if key.startswith(self.prefix+"-"):
#                     self.current_values[key.split(self.prefix+"-")[1]] = value
#
#         else:
#             # GET; initial was passed into constructor
#             self.current_values = self.initial

    def get_fields_from_list(self,field_list):
        return [field for field in self if field.name in field_list]

    def get_current_field_value(self, *args):
        """
        Return the field value from either "data" or "initial". The key will be reformatted to account for the form
        prefix.

        :param str key:
        :param default: If provided as a second argument, this value will be returned in case of a KeyError.

        >>> self.get_current_field_value('a')
        >>> self.get_current_field_value('a', None)
        """

        if len(args) == 1:
            key = args[0]
            has_default = False
        else:
            key, default = args
            has_default = True

        try:
            key_prefix = '{0}-{1}'.format(self.prefix, key)
            ret = self.data[key_prefix]
        except KeyError:
            try:
                ret = self.initial[key]
            except KeyError:
                if has_default:
                    ret = default
                else:
                    msg = 'The key "{0}" was not found in "data" or "initial" for form with prefix "{1}".'.format(key, self.prefix)
                    raise KeyError(msg)
        return ret


    def is_valid(self,*args,**kwargs):
        """
        Ensure that there are no id="None" in the data to be validated
        """

        id_key = self.prefix + "-id" if self.prefix else "id"
        if id_key in self.data:
            if self.data[id_key] == "None":
                self.data[id_key] = None

        return super(MetadataForm,self).is_valid(*args,**kwargs)


class MetadataCustomizerForm(MetadataForm):

    pass

class MetadataEditingForm(MetadataForm):

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