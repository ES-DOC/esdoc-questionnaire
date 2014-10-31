__author__="allyn.treshansky"
__date__ ="$Sep 30, 2013 4:12:23 PM$"

from django.conf import settings

from django.contrib.sites.models import Site

try:
    site = Site.objects.get(name=settings.SITE_NAME)
    settings.SITE_ID = site.pk
except Site.DoesNotExist:
    pass

APP_LABEL = "questionnaire"

__version_info__ = {
    'major': 0.11,
    'minor': 3,
    'patch': 0,
}

def get_version():
    version = ".".join(str(value) for value in __version_info__.values())
    return version

__version__ = get_version()
