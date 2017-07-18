####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

"""
.. module:: q_tags_admin

defines custom template tags for use in custom Q admin
(mostly for treating m2m fields as fk inlines - see "admin_proxies.py")
"""

from django import template
from django.core.urlresolvers import reverse
from Q.questionnaire.models.models_proxies import QModelProxy
from Q.questionnaire import APP_LABEL


MODEL_PROPERTY = QModelProxy.property_proxies.through
MODEL_CATEGORY = QModelProxy.category_proxies.through

register = template.Library()


@register.filter
def get_object_name(obj):
    if isinstance(obj, MODEL_PROPERTY):
        return obj.qpropertyproxy
    if isinstance(obj, MODEL_CATEGORY):
        return obj.qcategoryproxy
    return obj


@register.filter
def get_object_change_link(obj):
    if isinstance(obj, MODEL_PROPERTY):
        model_name = obj.qpropertyproxy._meta.model_name
        object_id = obj.qpropertyproxy.pk
    elif isinstance(obj, MODEL_CATEGORY):
        model_name = obj.qcategoryproxy._meta.model_name
        object_id = obj.qcategoryproxy.pk
    else:
        model_name = obj._meta.model_name
        object_id = obj.pk

    return reverse("admin:{0}_{1}_change".format(APP_LABEL, model_name), args=(object_id,))
