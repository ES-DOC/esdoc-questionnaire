####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

from django.forms import widgets
from django.db.models import QuerySet
from django.utils.html import format_html
from django.utils.encoding import force_text
from django.utils.functional import cached_property

from django.forms.fields import BooleanField
from django.forms.widgets import CheckboxInput
from django.forms.models import ModelForm, BaseModelFormSet, BaseInlineFormSet

from djangular.forms import NgModelFormMixin, NgFormValidationMixin, NgModelForm
from djangular.forms.angular_base import TupleErrorList
from djangular.styling.bootstrap3.forms import Bootstrap3ModelForm
from djangular.forms.angular_base import SafeTuple

from Q.questionnaire.q_utils import update_field_widget_attributes, set_field_widget_attributes
from Q.questionnaire.q_utils import QValidator

from djangular.styling.bootstrap3.field_mixins import BooleanFieldMixin
from djangular.styling.bootstrap3.widgets import CheckboxInput as BootstrapCheckBoxInput


# TODO: IS THIS FN USED?
def bootstrap_form(form):

    for field_name, field in form.fields.iteritems():
        bootstrap_field(field)

# TODO: IS THIS FN USED?
def bootstrap_field(field):
    bootstrap_classes = {
        "class": "form-control",
    }
    update_field_widget_attributes(field, bootstrap_classes)
    if not isinstance(field, BooleanField):
        set_field_widget_attributes(field, {
            "placeholder": field.label,
        })

# TODO: IS THIS FN USED?
def unbootstrap_field(field):
    if isinstance(field, BooleanField):
        # field.label = field.verbose_name
        # field.widget = CheckboxInput()
        pass

class QForm(Bootstrap3ModelForm, NgModelFormMixin, NgFormValidationMixin):
# class QForm(Bootstrap3ModelForm, NgFormValidationMixin):
# class QModelForm(NgModelForm, NgFormValidationMixin):
# class QModelForm(NgFormValidationMixin, NgModelForm):

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        form_name = kwargs.get("form_name", None)
        assert form_name, "QForm must have a unique name."

        super(QForm, self).__init__(*args, **kwargs)
        # add the possibility of rendering a server error on _all_ fields
        for field_name, field in self.fields.items():
            set_field_widget_attributes(field, {
                "servererror": "true",
            })
            # originally, I thought that I could specify a formset-specific "ng-model" attribute here
            # but that gets overwritten;
            # "ng-model" is set at the very-last-minute in djangular using the "get_widget_attrs" fn
            # so I overwrite _that_ fn below

    def get_widget_attrs(self, bound_field):
        """
        just like the base class fn
        except it sets "ng-model" using "get_qualified_model_field_name"
        (see comment in __init__ re: why I can't just override the attrs there)
        :param bound_field:
        :return: dictionary of field widget attrs
        """
        # note also that djangular overwrites widget classes further downstream
        # to get around this, with custom attributes,
        # I make sure to reset the "widget_css_classes" when calling set_widget_attributes or update_widget_attributes
        attrs = super(NgModelFormMixin, self).get_widget_attrs(bound_field)
        identifier = self.add_prefix(bound_field.name)
        ng = {
            'name': bound_field.name,
            'identifier': identifier,
            # here is the different bit:
            # 'model': self.scope_prefix and ('%s[\'%s\']' % (self.scope_prefix, identifier)) or identifier
            'model': self.get_qualified_model_field_name(bound_field.name)
        }
        if hasattr(self, 'Meta') and bound_field.name in getattr(self.Meta, 'ng_models', []):
            attrs['ng-model'] = ng['model']
        for key, fmtstr in self.ng_directives.items():
            attrs[key] = fmtstr % ng
        return attrs

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
            if self.prefix:
                key_prefix = '{0}-{1}'.format(self.prefix, key)
                ret = self.data[key_prefix]
            else:  # (the model_customizer_form does not have a prefix)
                ret = self.data[key]
        except KeyError:
            try:
                ret = self.initial[key]
            except KeyError:
                if has_default:
                    ret = default
                else:
                    msg = 'The key "{0}" was not found in "data" or "initial" for form of type {1} with prefix "{2}".'.format(key, type(self), self.prefix)
                    raise KeyError(msg)
        return ret

    def get_qualified_form_field_name(self, field_name):
        """
        gets a field name suitable for ng use when binding to form
        (must match the names in error handling)
        :param field_name:
        :return:
        """
        identifier = self.add_prefix(field_name)
        return format_html("{0}['{1}']", self.form_name, identifier)

    def get_qualified_model_field_name(self, field_name):
        """
        gets a field name suitable for ng use when binding to model
        (must match the names in $scopoe)
        :param field_name:
        :return:
        """
        # if self.is_formset():
        #     # the prefix is already handled implicitly in formsets
        #     identifier = field_name
        # else:
        #     identifier = self.add_prefix(field_name)
        identifier = field_name  # THIS ALLOWS ME TO STILL HAVE A UNIQUE PREFIX
        return format_html("{0}['{1}']", self.scope_prefix, identifier)

    def get_fields_from_list(self, field_names_list):
        """
        returns the fields corresponding to the names in field_names_list
        note that getting them explicitly as keys is more efficient than looping through self
        :param field_names_list:
        :return: fields corresponding to the names in field_names_list
        """
        fields = [self[field_name] for field_name in field_names_list]

        return fields

    def get_field_errors(self, bound_field):

        # identifier = format_html('{0}.{1}', self.form_name, bound_field.name)
        identifier = self.get_qualified_form_field_name(bound_field.name)
        error_list = self.errors.get(bound_field.html_name, [])
        errors = self.error_class([SafeTuple(
            (identifier, self.field_error_css_classes, '$pristine', '$pristine', 'invalid', e)) for e in error_list])

        if bound_field.is_hidden:
            return errors
        # identifier = format_html('{0}.{1}', self.form_name, self.add_prefix(bound_field.name))
        identifier = self.get_qualified_form_field_name(bound_field.name)

        potential_errors = bound_field.field.get_potential_errors()
        errors.extend([SafeTuple((identifier, self.field_error_css_classes, '$dirty', pe[0], 'invalid', force_text(pe[1])))
                       for pe in potential_errors])

        if not isinstance(bound_field.field.widget, widgets.PasswordInput):
            # all valid fields shall display OK tick after changed into dirty state
            errors.append(SafeTuple((identifier, self.field_error_css_classes, '$dirty', '$valid', 'valid', '')))
            if bound_field.value():
                # valid bound fields shall display OK tick, even in pristine state
                errors.append(SafeTuple((identifier, self.field_error_css_classes, '$pristine', '$valid', 'valid', '')))

        self.add_custom_errors(errors, bound_field)

        return errors

    def add_custom_errors(self, existing_errors, bound_field):
        """
        called by get_field_errors
        ensures custom client-side validation AND server-side validation is taken into account
        :param existing_errors:
        :param bound_field:
        :return:
        """
        identifier = self.get_qualified_form_field_name(bound_field.name)

        # add custom client-side validation as needed...
        custom_potential_errors = getattr(bound_field.field, "custom_potential_errors", [])
        if custom_potential_errors:
            # TODO: MAY WANT TO CHANGE THIS STRING TO BETTER WORK W/ ng-model
            existing_errors.extend([
                SafeTuple((identifier, self.field_error_css_classes, '$dirty', '$error.%s' % pe.name, 'invalid', pe.msg,))
                for pe in custom_potential_errors
            ])

        # add server-side validation as needed...
        server_error = "servererror"
        if server_error in bound_field.field.widget.attrs:
            # TODO: I'M NOT SURE WHY I NEED "{% verbatim ng %}" WHEN ADDED DIRECTLY TO THE TEMPLATE, BUT NOT HERE
            # server_error_msg = "{% verbatim ng %} {{ server_errors.model_customization.whatever }} {% endverbatim ng %}"
            # to escape curly brackets, I have to double them...
            # server_error_msg = "{{{{ server_errors.model_customization.{0} }}}}".format(bound_field.name)
            server_error_msg = "{{{{ server_errors.{0} }}}}".format(self.get_qualified_model_field_name(bound_field.name))
            existing_errors.append(
                SafeTuple((identifier, self.field_error_css_classes, '$dirty', '$error.server', "invalid", server_error_msg))
            )

        return existing_errors

    def add_custom_potential_errors_to_field(self, field_name):

        form_field = self.fields[field_name]
        model_field = self.instance.get_field(field_name)

        # only check fields that have a correspondance to the model,
        # and that can be edited by the user...
        if model_field is not None and model_field.editable:

            custom_validators = [v for v in model_field.validators if isinstance(v, QValidator)]
            for validator in custom_validators:
                # this attribute is required for Angular to know about the custom validator
                set_field_widget_attributes(form_field, {validator.name: "true"})

            # and I store the validators for later use in get_field_errors() above
            setattr(form_field, "custom_potential_errors", custom_validators)

    def unbootstrap_fields(self, field_names):
        for field_name in field_names:
            self.unbootstrap_field(field_name)

    def unbootstrap_field(self, field_name):

        # QForm form inherits from Bootstrap3ModelForm;
        # this means that funny things happen automatically when rendering fields
        # this fn can undo those things on a per-field basis

        form_field = self.fields[field_name]
        model_field = self.instance.get_field(field_name)

        if isinstance(form_field, BooleanField):
            # boolean fields include the label_tag as part of the widget and delete the label on the main field
            # that's not desired Q behavior (it messes up alignment of form labels & widgets)
            # so this code puts everything back
            form_field.widget = CheckboxInput(attrs=form_field.widget.attrs)
            form_field.label = model_field.verbose_name

        else:
            # TODO: ANY OTHER FIXES FOR OTHER FIELD TYPES?
            pass

    def is_new(self):
        return self.instance.pk is None

    def is_existing(self):
        return not self.is_new()

class QFormSet(BaseModelFormSet):

    def __init__(self, *args, **kwargs):
        kwargs.update({
            # makes sure that child forms render errors correctly...
            # TODO: THIS IS ACTUALLY THE FIX FOR A BUG IN DJANGULAR (https://github.com/jrief/django-angular/issues/197)
            # TODO: I SHOULD PATCH THAT PROJECT
            "error_class": TupleErrorList,
        })
        super(QFormSet, self).__init__(*args, **kwargs)

    # def __iter__(self):
    #     """Yields the forms in the order they should be rendered"""
    #     return iter(self.forms)

    # @cached_property
    # def forms(self):
    #     """
    #     Instantiate forms at first property access.
    #     """
    #     # DoS protection is included in total_form_count()
    #     forms = [self._construct_form(i) for i in range(self.total_form_count())]
    #     return forms

    def get_queryset(self):
        # since the underlying queryset for a QFormSet may actually be a list
        # - due to my use of a custom manager for unsaved models -
        # I have to overwrite this fn to not try to use Queryset-specific ordering methods
        # (mostly, though, this code is taken from "django.forms.models.BaseModelFormSet#get_queryset")
        if not hasattr(self, '_queryset'):
            if self.queryset is not None:
                qs = self.queryset
            else:
                qs = self.model._default_manager.get_queryset()

            # If the queryset isn't already ordered we need to add an
            # artificial ordering here to make sure that all formsets
            # constructed from this queryset have the same form order.
            # HERE BEGINS THE DIFFERENT BIT
            if isinstance(qs, QuerySet) and not qs.ordered:
                qs = qs.order_by(self.model._meta.pk.name)
            # HERE ENDS THE DIFFERENT BIT

            # Removed queryset limiting here. As per discussion re: #13023
            # on django-dev, max_num should not prevent existing
            # related objects/inlines from being displayed.
            self._queryset = qs

        return self._queryset

    def _construct_form(self, i, **kwargs):
        """
        instantiates and returns the ith form instance in a formset
        :param i:
        :param kwargs:
        :return:
        """
        if self.is_bound and i < self.initial_form_count():
            pk_key = "%s-%s" % (self.add_prefix(i), self.model._meta.pk.name)
            pk = self.data[pk_key]
            pk_field = self.model._meta.pk
            to_python = self._get_to_python(pk_field)
            pk = to_python(pk)
            kwargs['instance'] = self._existing_object(pk)
        if i < self.initial_form_count() and 'instance' not in kwargs:
            kwargs['instance'] = self.get_queryset()[i]
        if i >= self.initial_form_count() and self.initial_extra:
            # Set initial values for extra forms
            try:
                kwargs['initial'] = self.initial_extra[i - self.initial_form_count()]
            except IndexError:
                pass

        # THIS IS THE DIFFERENT BIT
        # I MAKE SURE THAT THE CORRECT error_class IS USED FOR NG FORMS
        # AND THEN I ADD A scope_prefix AND UNIQUE form_name USING add_default_form_arguments BELOW
        defaults = {
            'auto_id': self.auto_id,
            'prefix': self.add_prefix(i),
            'error_class': self.error_class,  # see __init__ above; self.error_class = TupleErrorList
        }
        defaults.update(self.add_default_form_arguments(i))
        # THIS ENDS THE DIFFERENT BIT

        if self.is_bound:
            defaults['data'] = self.data
            defaults['files'] = self.files
        if self.initial and 'initial' not in kwargs:
            try:
                defaults['initial'] = self.initial[i]
            except IndexError:
                pass
        # Allow extra forms to be empty, unless they're part of
        # the minimum forms.
        if i >= self.initial_form_count() and i >= self.min_num:
            defaults['empty_permitted'] = True
        defaults.update(kwargs)
        form = self.form(**defaults)
        self.add_fields(form, i)
        return form

    def add_default_form_arguments(self, i):
        """
        adds ng-specific kwargs to the child form class
        (called by "_construct_form")
        in this case, I am adding a scope_prefix and a unique name
        :param i: index of form to be constructed
        :return: kwarg dict
        """
        additional_default_form_arguments = {
            'scope_prefix': "{0}[{1}]".format(self.scope_prefix, i),
            'form_name': "{0}_{1}".format(self.formset_name, i),
        }
        return additional_default_form_arguments

    def add_prefix(self, index):
        """
        ng can't cope w/ hyphens in variable names, b/c that's invalid javascript
        (although, really, it's just the form names that this is an issue for; and that's been hard-coded in '_construct_form' above)
        (overriding this fn just offers some protection in case I decide to write some really clever ng code later)
        :param index:
        :return:
        """
        prefix = super(QFormSet, self).add_prefix(index)
        ng_prefix = prefix.replace('-', '_')
        return ng_prefix

##########
# originally, a lot of effort was spent getting Djangular Forms to work in InlineFormSets
# however, this is no longer the case so this code is commented out
# however, still, it's good code and I keep it here in-case things ever change
##########

# class QInlineFormSet(BaseInlineFormSet):
#
#     # a label and some help_text can be defined on the entire formset
#     # (to be used in the templates)
#     label = ""
#     help_text = ""
#
#     def __init__(self, *args, **kwargs):
#         initial = kwargs.get("initial")
#         queryset = kwargs.get("queryset")
#         label = kwargs.pop("label", None)
#         help_text = kwargs.pop("help_text", None)
#         kwargs.update({
#             # makes sure that child forms render errors correctly...
#             # TODO: THIS IS ACTUALLY THE FIX FOR A BUG IN DJANGULAR (https://github.com/jrief/django-angular/issues/197)
#             # TODO: I SHOULD PATCH THAT PROJECT
#             "error_class": TupleErrorList,
#         })
#         super(QInlineFormSet, self).__init__(*args, **kwargs)
#
#         self.current_form_index = 0
#         self.label = label or self.label
#         self.help_text = help_text or self.help_text
#
#         if initial and not queryset:
#             # djangular assumes that "initial" data will be used to populate default formset values
#             # but I use it to transfer proxy data to forms; this works well w/ the "extra" kwargs
#             # anyway, self.initial gets overwritten somewhere in the djangular setup
#             # this code resets it so that other djangular fns (like get_initial_data) will work
#             assert self.extra == self.total_form_count() == len(initial)
#             self.num_forms = len(initial)
#             self.initial = self.initial_extra
#         if queryset and not initial:
#             assert self.total_form_count() == queryset.count()
#             self.num_forms = queryset.count()
#
#     # thought about caching the forms fn
#     # turns out, BaseFormSet already uses the "@cached_property" decorator
#
#     def get_next_form(self):
#         next_form = self.forms[self.current_form_index % self.num_forms]
#         self.current_form_index += 1
#         return next_form
#
#     def get_form_by_field(self, field_name, field_value):
#         for form in self.forms:
#             if form.get_current_field_value(field_name) == field_value:
#                 return form
#         return None
#
#     def get_forms_by_field(self, field_name, field_value):
#         forms = []
#         for form in self.forms:
#             if form.get_current_field_value(field_name) == field_value:
#                 forms.append(form)
#         return forms
#
#     def get_initial_data(self):
#         initial_data = [
#             form.get_initial_data()
#             for form in self.forms
#         ]
#         return initial_data
#
#     # this took a while to figure out
#     # I need to add some special kwargs when instantiating a child form
#     # but that actually gets handled by the 3rd parent in the inheritance tree's "_construct_form" fn
#     # (QInlineFormSet::BaseInlineFormset::BaseModelFormSet::BaseFormset)
#     # this "_construct_form" fn does all of the stuff that BaseInlineFormSet & BaseModelFormset do in their "_construct_form" fn
#     # then it calls "_construct_q_form" which is does slightly different stuff than BaseFormset does in its "_construct_form" fn
#
#     def _construct_form(self, i, **kwargs):
#         """
#         just like BaseInlineFormSet method
#         except calls "_construct_q_form" below
#         :param i:
#         :param kwargs:
#         :return:
#         """
#         # form = super(BaseInlineFormSet, self)._construct_form(i, **kwargs)
#         # this bit comes from BaseModelFormSet...
#         if self.is_bound and i < self.initial_form_count():
#             pk_key = "%s-%s" % (self.add_prefix(i), self.model._meta.pk.name)
#             pk = self.data[pk_key]
#             pk_field = self.model._meta.pk
#             to_python = self._get_to_python(pk_field)
#             pk = to_python(pk)
#             kwargs['instance'] = self._existing_object(pk)
#         if i < self.initial_form_count() and 'instance' not in kwargs:
#             kwargs['instance'] = self.get_queryset()[i]
#         if i >= self.initial_form_count() and self.initial_extra:
#             # Set initial values for extra forms
#             try:
#                 kwargs['initial'] = self.initial_extra[i - self.initial_form_count()]
#             except IndexError:
#                 pass
#         # ...end this bit comes from BaseModelFormset
#
#         # here's what I do instead of "BaseFormSet._construct_form()"...
#         form = self._construct_q_form(i, **kwargs)
#
#         if self.save_as_new:
#             # Remove the primary key from the form's data, we are only
#             # creating new instances
#             form.data[form.add_prefix(self._pk_field.name)] = None
#
#             # Remove the foreign key from the form's data
#             form.data[form.add_prefix(self.fk.name)] = None
#
#         # Set the fk value here so that the form can do its validation.
#         fk_value = self.instance.pk
#         if self.fk.rel.field_name != self.fk.rel.to._meta.pk.name:
#             fk_value = getattr(self.instance, self.fk.rel.field_name)
#             fk_value = getattr(fk_value, 'pk', fk_value)
#         setattr(form.instance, self.fk.get_attname(), fk_value)
#         return form
#
#     def _construct_q_form(self, i, **kwargs):
#         """
#         just like BaseFormSet _construct_form
#         except adds some kwargs to "defaults" for QForm instances
#         called by "_construct_form" above
#         """
#
#         defaults = {
#             'auto_id': self.auto_id,
#             'prefix': self.add_prefix(i),
#             'error_class': self.error_class,  # see above; error_class = TupleErrorList
#             # the next 2 lines of code are the different bits...
#             # TODO: THIS ISN'T QUITE RIGHT YET, IS IT?
#             'scope_prefix': "%s[%d]" % (self.scope_prefix, i),
#             'form_name': "%s_%s" % (self.formset_name, i),  # ensure a unique form name, and doesn't use hyphens (which are invalid in js and, therefore, ng)
#
#         }
#         if self.is_bound:
#             defaults['data'] = self.data
#             defaults['files'] = self.files
#         if self.initial and 'initial' not in kwargs:
#             try:
#                 defaults['initial'] = self.initial[i]
#             except IndexError:
#                 pass
#         # Allow extra forms to be empty, unless they're part of
#         # the minimum forms.
#         if i >= self.initial_form_count() and i >= self.min_num:
#             defaults['empty_permitted'] = True
#         defaults.update(kwargs)
#         form = self.form(**defaults)
#         self.add_fields(form, i)
#         return form
#
#     def add_prefix(self, index):
#         """
#         ng can't cope w/ hyphens in variable names, b/c that's invalid javascript
#         (although, really, it's just the form names that this is an issue for; and that's been hard-coded in _construct_form above)
#         :param index:
#         :return:
#         """
#         prefix = super(QInlineFormSet, self).add_prefix(index)
#         ng_prefix = prefix.replace('-', '_')
#         return ng_prefix