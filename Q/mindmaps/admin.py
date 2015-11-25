from django.contrib import admin

from .models import MindMapSource, MindMapDomain

class MindMapDomainAdmin(admin.TabularInline):
    model = MindMapDomain

class MindMapSourceAdmin(admin.ModelAdmin):
    inlines = (MindMapDomainAdmin, )

admin.site.register(MindMapSource, MindMapSourceAdmin)
