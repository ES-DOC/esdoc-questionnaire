
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from CIM_Questionnaire.questionnaire.models import *

esfdl=MetadataProject.objects.get(name__iexact="es-fdl")
downscaling=MetadataProject.objects.get(name__iexact="downscaling")
cim_1_10=MetadataVersion.objects.get(version="1.10")
proxy=MetadataModelProxy.objects.get(version=cim_1_10,name__iexact="modelcomponent")
esfdl_customizer=MetadataModelCustomizer.objects.get(project=esfdl,proxy=proxy,default=True)
downscaling_customizer=MetadataModelCustomizer.objects.get(project=downscaling,proxy=proxy,default=True)
downscaling_scientific_category_customizers=downscaling_customizer.scientific_property_category_customizers.all()
esfdl_scientific_category_customizers=esfdl_customizer.scientific_property_category_customizers.all()

for category_customizer in downscaling_scientific_category_customizers:
  assert(category_customizer.model_customizer == downscaling_customizer)
  assert(category_customizer.project == downscaling)
  assert(category_customizer.project == category_customizer.model_customizer.project)
for category_customizer in esfdl_scientific_category_customizers:
  assert(category_customizer.model_customizer == esfdl_customizer)
  assert(category_customizer.project == esfdl)
  assert(category_customizer.project == category_customizer.model_customizer.project)

