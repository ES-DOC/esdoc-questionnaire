#! /usr/bin/python

__author__="allyn.treshansky"
__date__ ="$Jan 15, 2014 15:28:06 PM$"

import os

from uuid import uuid4

if __name__ == "__main__":

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    # can only import django stuff after DJANGO_SETTINGS_MODULE has been set
    # (also - since this is run outside of server context - the settings module will fail on some imports;
    # hence the try/except block in settings.py for "fixing known django / south / postgres issue")

    from django.contrib.contenttypes.models import ContentType

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
