#! /usr/bin/python

__author__ = "allyn.treshansky"
__date__ = "$Jan 15, 2014 15:28:06 PM$"

import os

from uuid import uuid4

if __name__ == "__main__":

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    # can only import django stuff after DJANGO_SETTINGS_MODULE has been set
    # (also - since this is run outside of server context - the settings module will fail on some imports;
    # hence the try/except block in settings.py for "fixing known django / south / postgres issue")

    from django.contrib.contenttypes.models import ContentType
    from django.template.defaultfilters import slugify

    from CIM_Questionnaire.questionnaire.models import *

    ComponentClass = ContentType.objects.get(app_label="questionnaire", model="metadatacomponentproxy").model_class()
    component_qs = ComponentClass.objects.all()
    for component in component_qs:
        if not component.guid:
            component.guid = str(uuid4())
            component.save()

    VocabularyClass = ContentType.objects.get(app_label="questionnaire", model="metadatavocabulary").model_class()
    vocabulary_qs = VocabularyClass.objects.all()
    for vocabulary in vocabulary_qs:
        if not vocabulary.guid:
            vocabulary.guid = str(uuid4())
            vocabulary.save()

    for vocabulary in MetadataVocabulary.objects.all():

        old_vocabulary_key = slugify(vocabulary.name)
        new_vocabulary_key = vocabulary.get_key()

        for component in vocabulary.component_proxies.all():

            old_component_key = slugify(component.name)
            new_component_key = component.get_key()

            scientific_category_customizers = MetadataScientificCategoryCustomizer.objects.filter(vocabulary_key=old_vocabulary_key, component_key=old_component_key)
            for scientific_category_customizer in scientific_category_customizers:
                scientific_category_customizer.vocabulary_key = new_vocabulary_key
                scientific_category_customizer.component_key = new_component_key
                scientific_category_customizer.model_key = u"%s_%s" % (new_vocabulary_key, new_component_key)
                scientific_category_customizer.save()

            scientific_property_customizers = MetadataScientificPropertyCustomizer.objects.filter(vocabulary_key=old_vocabulary_key, component_key=old_component_key)
            for scientific_property_customizer in scientific_property_customizers:
                scientific_property_customizer.vocabulary_key = new_vocabulary_key
                scientific_property_customizer.component_key = new_component_key
                scientific_property_customizer.model_key = u"%s_%s" % (new_vocabulary_key, new_component_key)
                scientific_property_customizer.save()

            models = MetadataModel.objects.filter(vocabulary_key=old_vocabulary_key, component_key=old_component_key)
            for model in models:
                model.vocabulary_key = new_vocabulary_key
                model.component_key = new_component_key
                model.save()


    for model in MetadataModel.objects.all():
        if not model.guid:
            model.guid = str(uuid4())
            model.save()
