__author__ = 'allyn.treshansky'

from django.conf import settings
from django.contrib.sites.models import Site

#from CIM_Questionnaire.questionnaire.utils import QuestionnaireError

class DynamicSitesMiddleware(object):

    def process_request(self, request):
        domain = request.get_host()
        try:
            current_site = Site.objects.get(domain=domain)
        except Site.DoesNotExist:
            msg = "Unable to locate domain '%s' in Sites.  Please update the database." % (domain)
            #raise QuestionnaireError(msg)
            print msg
            current_site = Site.objects.get(id=settings.DEFAULT_SITE_ID)

        request.current_site = current_site
        settings.SITE_ID = current_site.id
