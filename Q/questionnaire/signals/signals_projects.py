####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2015 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

from django.db.models.signals import post_save, post_delete

from Q.questionnaire.models.models_customizations import QModelCustomization, QModelCustomizationVocabulary
from Q.questionnaire.models.models_realizations import QModel

from Q.questionnaire.models.models_projects import QProject, QProjectVocabulary, GROUP_PERMISSIONS

def post_save_project_handler(sender, **kwargs):
    """
    fn that gets called after a QProject is saved;
    if it's just been created, then the corresponding permissions and groups need to be setup
    :param sender:
    :param kwargs:
    :return:
    """
    created = kwargs.pop("created", True)
    project = kwargs.pop("instance", None)
    if project and created:
        for group_suffix, permission_prefixes in GROUP_PERMISSIONS.iteritems():
            group = project.get_group(group_suffix, create_group=True)
            for permission_prefix in permission_prefixes:
                permission = project.get_permission(permission_prefix, create_permission=True)
                group.permissions.add(permission)
            group.save()

post_save.connect(
    post_save_project_handler,
    sender=QProject,
    dispatch_uid="post_save_project_handler"
)

def post_delete_project_handler(sender, **kwargs):
    """
    fn that gets called after a QProject is deleted;
    the corresponding permissions and groups need to be deleted
    :param sender:
    :param kwargs:
    :return:
    """
    project = kwargs.pop("instance", None)
    if project:
        groups = [project.get_group(group_suffix) for group_suffix in GROUP_PERMISSIONS.keys()]
        permissions = set([permission for group in groups for permission in group.permissions.all()])
        for permission in permissions:
            permission.delete()
        for group in groups:
            group.delete()

post_delete.connect(
    post_delete_project_handler,
    sender=QProject,
    dispatch_uid="post_delete_project_handler"
)


# I originally wanted to use the standard m2m_changed signal
# to track when QVocabularies are added/removed to/from QProjects
# but that clears the entire relationship before re-adding models
# which is extremely inefficient; so instead I use a "through" model
# (QProjectVocabulary) and use these save/delete signals on that model

def post_save_projectvocabulary_handler(sender, **kwargs):
    created = kwargs.pop("created", True)
    projectvocabulary = kwargs.pop("instance", None)
    if projectvocabulary and created:
        project = projectvocabulary.project
        vocabulary = projectvocabulary.vocabulary

        customizations_to_update = QModelCustomization.objects.filter(
            project=project,
            proxy__name__iexact=vocabulary.document_type
        )
        for customization in customizations_to_update:
            (model_customization_vocabulary, created_model_customization_vocabulary) = QModelCustomizationVocabulary.objects.get_or_create(
                model_customization=customization,
                vocabulary=vocabulary,
            )
            if created_model_customization_vocabulary:
                customization.updated_vocabulary(model_customization_vocabulary)

        # TODO: DO THE SAME THING FOR REALIZATIONS...

post_save.connect(
    post_save_projectvocabulary_handler,
    sender=QProject.vocabularies.through,
    dispatch_uid="post_save_projectvocabulary_handler"
)


def post_delete_projectvocabulary_handler(sender, **kwargs):
    projectvocabulary = kwargs.pop("instance", None)
    if projectvocabulary:
        project = projectvocabulary.project
        vocabulary = projectvocabulary.vocabulary

        # customizations_to_update = QModelCustomization.objects.filter(
        #     project=project,
        #     # TODO: TEST THAT THIS SYNTAX WORKS EVEN W/OUT A "related_name" ARGUMENT IN THE THROUGH MODEL
        #     I AM HERE
        #     vocabularies__in=[vocabulary],
        # )
        # for customization in customizations_to_update:
        #     customization.removed_vocabulary(vocabulary)
        #
        # # TODO: DO THE SAME THING FOR REALIZATIONS...


post_delete.connect(
    post_delete_projectvocabulary_handler,
    sender=QProject.vocabularies.through,
    dispatch_uid="post_delete_projectvocabulary_handler"
)
