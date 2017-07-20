####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_delete, post_delete

from Q.questionnaire.models.models_projects import QProject, QProjectOntology, GROUP_PERMISSIONS
from Q.questionnaire import APP_LABEL


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
    if created:
        assert project.groups.count() == 0
        for group_suffix, permission_prefixes in GROUP_PERMISSIONS.iteritems():
            group_name = "{0}_{1}".format(project.name, group_suffix)
            group = Group(
                name=group_name
            )
            group.save()
            for permission_prefix in permission_prefixes:
                permission_codename = "{0}_{1}".format(permission_prefix, project.name)
                permission_description = "{0} {1} instances".format(permission_prefix, project.name)
                content_type = ContentType.objects.get(app_label=APP_LABEL, model='qproject')
                (permission, created_permission) = Permission.objects.get_or_create(
                    codename=permission_codename,
                    name=permission_description,
                    content_type=content_type,
                )
                group.permissions.add(permission)
            group.save()
            project.groups.add(group)

post_save.connect(
    post_save_project_handler,
    sender=QProject,
    dispatch_uid="post_save_project_handler"
)


def pre_delete_project_handler(sender, **kwargs):
    """
    fn that gets called before a QProject is deleted;
    the corresponding permissions and groups need to be explicitly deleted
    :param sender:
    :param kwargs:
    :return:
    """
    project = kwargs.pop("instance", None)
    if project:
        groups = project.groups.all()
        permissions = set([permission for group in groups for permission in group.permissions.all()])
        for permission in permissions:
            permission.delete()
        for group in groups:
            group.delete()

pre_delete.connect(
    pre_delete_project_handler,
    sender=QProject,
    dispatch_uid="pre_delete_project_handler"
)


def post_delete_project_handler(sender, **kwargs):
    """
    fn that gets called after a QProject is deleted;
    the order of all other projects may need to be updated
    :param sender:
    :param kwargs:
    :return:
    """
    project = kwargs.pop("instance", None)
    if project:
        for p in QProject.objects.filter(order__gt=project.order):
            p.order -= 1
            p.save()


post_delete.connect(
    post_delete_project_handler,
    sender=QProject,
    dispatch_uid="post_delete_project_handler"
)

# I originally wanted to use the standard m2m_changed signal
# to track when QOntologies are added/removed to/from QProjects
# but that clears the entire relationship before re-adding models
# which is extremely inefficient; so instead I use a "through" model
# (QProjectOntology) and use these save/delete signals on that model

# def post_save_projectontology_handler(sender, **kwargs):
#     created = kwargs.pop("created", True)
#     projectontology = kwargs.pop("instance", None)
#     if projectontology and created:
#         project = projectontology.project
#         ontology = projectontology.ontology
#
#         # TODO: UPDATE CUSTOMIZATIONS
#         # customizations_to_update = QModelCustomization.objects.filter(
#         #     project=project,
#         #     proxy__name__iexact=vocabulary.document_type
#         # )
#         # for customization in customizations_to_update:
#         #     (model_customization_vocabulary, created_model_customization_vocabulary) = QModelCustomizationVocabulary.objects.get_or_create(
#         #         model_customization=customization,
#         #         vocabulary=vocabulary,
#         #     )
#         #     if created_model_customization_vocabulary:
#         #         customization.updated_vocabulary(model_customization_vocabulary)
#         #
#         # TODO: DO THE SAME THING FOR REALIZATIONS...
#
# post_save.connect(
#     post_save_projectontology_handler,
#     sender=QProject.ontologies.through,
#     dispatch_uid="post_save_projectontology_handler"
# )


# def post_delete_projectontology_handler(sender, **kwargs):
#     projectontology = kwargs.pop("instance", None)
#     if projectontology:
#         project = projectontology.project
#         ontology = projectontology.ontology
#
#         # customizations_to_update = QModelCustomization.objects.filter(
#         #     project=project,
#         #     # TODO: TEST THAT THIS SYNTAX WORKS EVEN W/OUT A "related_name" ARGUMENT IN THE THROUGH MODEL
#         #     I AM HERE
#         #     vocabularies__in=[vocabulary],
#         # )
#         # for customization in customizations_to_update:
#         #     customization.removed_vocabulary(vocabulary)
#         #
#         # # TODO: DO THE SAME THING FOR REALIZATIONS...
#
#
# post_delete.connect(
#     post_delete_projectontology_handler,
#     sender=QProject.ontologies.through,
#     dispatch_uid="post_delete_projectontology_handler"
# )
