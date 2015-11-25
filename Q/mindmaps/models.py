from django.db import models

class MindMapSource(models.Model):
    class Meta:
        verbose_name = "MindMap Source"
        verbose_name_plural = "MindMap Sources"

    name = models.CharField(max_length=64, blank=False, null=False, unique=True)
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return u"%s" % self.name


class MindMapDomain(models.Model):
    class Meta:
        verbose_name = "MindMap Domain"
        verbose_name_plural = "MindMap Domains"

    domain = models.URLField(blank=False)
    source = models.ForeignKey("MindMapSource", related_name="domains")

    def __unicode__(self):
        return u"%s" % self.domain
