from django.contrib import admin

from models import *

#admin.site.register(MetadataCV)

admin.site.register(DataSource)
admin.site.register(DateRange)
admin.site.register(Calendar)
admin.site.register(DataObject)
admin.site.register(CompositeNumericalRequirement)
admin.site.register(NumericalRequirement)
admin.site.register(RequirementOption)
admin.site.register(NumericalExperiment)
admin.site.register(TimeTransformation)
admin.site.register(CouplingEndPoint)
admin.site.register(Coupling)
admin.site.register(Conformance)
admin.site.register(SimulationRun)
admin.site.register(ComponentLanguage)
admin.site.register(ResponsibleParty)
admin.site.register(Citation)
admin.site.register(Timing)
admin.site.register(TimeLag)
admin.site.register(SpatialRegriddingUserMethod)
admin.site.register(SpatialRegridding)
admin.site.register(ModelComponent)
