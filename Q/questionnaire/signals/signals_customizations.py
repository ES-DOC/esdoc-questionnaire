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

from django.db.models.signals import post_save, post_delete
from django.dispatch import Signal

from Q.questionnaire.models.models_customizations import QModelCustomization, QModelCustomizationVocabulary

def post_save_modelcustomizationvocabulary_handler(sender, **kwargs):
    """
    fn to run when I save a QModelCustomizationVocabulary
    (this is the "through" model on the QModelCustomization to QVocabulary relationship)
    whenever I add to that relationship, I make sure to update the through models' order
    :param sender:
    :param kwargs:
    :return:
    """
    created = kwargs.pop("created", True)
    model_customization_vocabulary = kwargs.pop("instance", None)
    if model_customization_vocabulary and created:
        model_customization = model_customization_vocabulary.model_customization
        model_customization.update_vocabulary_order()

post_save.connect(
    post_save_modelcustomizationvocabulary_handler,
    sender=QModelCustomization.vocabularies.through,
    dispatch_uid="post_save_modelcustomizationvocabulary_handler"
)


def post_delete_modelcustomizationvocabulary_handler(sender, **kwargs):
    """
    fn to run when I delete a QModelCustomizationVocabulary
    (this is the "through" model on the QModelCustomization to QVocabulary relationship)
    whenever I remove from that relationship, I make sure to update the through models' order
    :param sender:
    :param kwargs:
    :return:
    """
    model_customization_vocabulary = kwargs.pop("instance", None)
    if model_customization_vocabulary:
        model_customization = model_customization_vocabulary.model_customization
        model_customization.update_vocabulary_order()

post_delete.connect(
    post_delete_modelcustomizationvocabulary_handler,
    sender=QModelCustomization.vocabularies.through,
    dispatch_uid="post_delete_modelcustomizationvocabulary_handler"
)


# thought about adding a signal for when subform_customizations are added to standard_property_customizations
# but that was a lot of work just to add an attribute to the parent property;
# instead this is done explicitly in "get_new_customization_set"
# def added_subform_handler(sender, **kwargs):
#     subform_customization = kwargs.pop("instance", None)
#     parent_property = kwargs.pop("parent_property", None)
#     assert subform_customization and parent_property
#     parent_property.subform_customization = subform_customization
#
# added_subform_signal = Signal(providing_args=["parent_property"])
# added_subform_signal.connect(
#     added_subform_handler,
#     sender=QModelCustomization,
#     dispatch_uid="added_subform_hander"
# )