
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Q.settings")


from Q.questionnaire.models import *

projects = QProject.objects.all()

for _project in projects:

    _model_customizers = _project.model_customizers.all()
    for _model_customizer in _model_customizers:
        scientific_category_customizers = _model_customizer.scientific_property_category_customizers.all()
        for scientific_category_customizer in scientific_category_customizers:
            scientific_category_proxy = scientific_category_customizer.proxy
            scientific_category_customizer.key = scientific_category_proxy.key
            scientific_category_customizer.save()

    _models = _project.models.all()
    for _model in _models:
        scientific_properties = _model.scientific_properties.all()
        for scientific_property in scientific_properties:
            scientific_category_proxy = scientific_property.proxy.category
            scientific_property.category_key = scientific_category_proxy.key
            scientific_property.save()
