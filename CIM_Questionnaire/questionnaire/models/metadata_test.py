__author__ = 'allyn.treshansky'

from django.db import models

from CIM_Questionnaire.questionnaire.utils import APP_LABEL

class Person(models.Model):

    class Meta:
        app_label = APP_LABEL

    name = models.CharField(max_length=64)

    def __unicode__(self):
        return u"%s" % (self.name)

class Book(models.Model):

    class Meta:
        app_label = APP_LABEL

    name = models.CharField(max_length=64)
    author = models.ForeignKey("Person",blank=True,null=True)
    library = models.ForeignKey("Library",blank=False,null=True,related_name="books")

    def __unicode__(self):
        return u"%s" % (self.name)

    def reset(self):
        author = self.author
        if author:
            self.author = author

class Library(models.Model):

    class Meta:
        app_label = APP_LABEL

    name = models.CharField(max_length=64)

    def __unicode__(self):
        return u"%s" % (self.name)
