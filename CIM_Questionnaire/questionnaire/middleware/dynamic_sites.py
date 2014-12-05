####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2014 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"
__date__ = "Dec 01, 2014 3:00:00 PM"

"""
.. module:: dynamic_sites

Sets current site dynamically on a per-request basis.
This is needed b/c the site information is used for various messages that get emailed to administrators
(such as project join requests); In order to process the request, recipients must know which site to act upon.
"""

from django.conf import settings
from django.contrib.sites.models import Site
#from CIM_Questionnaire.questionnaire.utils import QuestionnaireError


class DynamicSitesMiddleware(object):

    def process_request(self, request):

        """
        Intercepts request as per standard Django middleware
        Tries to find a site in the db based on the request's domain
        :param request:
        :return:
        """

        domain = request.get_host()
        try:
            current_site = Site.objects.get(domain=domain)
        except Site.DoesNotExist:
            # rather than raising an error, just use site w/ a pk=1 (as per settings.DEFAULT_SITE_ID)
            #msg = "Unable to locate domain '%s' in Sites.  Please update the database." % domain
            #raise QuestionnaireError(msg)

            current_site = Site.objects.get(id=settings.DEFAULT_SITE_ID)

        request.current_site = current_site
        settings.SITE_ID = current_site.id
