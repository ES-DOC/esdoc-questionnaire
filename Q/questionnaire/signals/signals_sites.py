####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = 'allyn.treshansky'

from django.db.models.signals import post_save
from django.db.utils import ProgrammingError
from django.contrib.sites.models import Site

from Q.questionnaire.models.models_sites import QSite
from Q.questionnaire.q_utils import QError

def post_save_site_handler(sender, **kwargs):
    """
    fn that gets called after a standard Django Site is saved;
    if it's just been created, then the corresponding QSite needs to be setup
    :param sender:
    :param kwargs:
    :return:
    """
    created = kwargs.pop("created", True)
    site = kwargs.pop("instance", None)
    if site and created:
        try:
            (q_site, created_q_site) = QSite.objects.get_or_create(site=site)
        except ProgrammingError:
            if site.pk == 1:
                # this might fail during initial migration b/c the full set of db tables will not have been setup yet
                print("skipped creating site profile for %s" % (site))
                pass
            else:
                msg = "Unable to create site profile for %s" % (site)
                raise QError(msg)


post_save.connect(post_save_site_handler, sender=Site, dispatch_uid="post_save_site_handler")
