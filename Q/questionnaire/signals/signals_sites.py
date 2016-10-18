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
from Q.questionnaire.signals.signals_base import disable_for_fixtures
from Q.questionnaire.q_utils import QError


@disable_for_fixtures
def post_save_site_handler(sender, instance, created, **kwargs):
    """
    fn that gets called after a standard Django Site is saved;
    if it's just been created, then the corresponding QSite needs to be setup
    :param sender:
    :param kwargs:
    :return:
    """
    if instance and created:
        try:
            (q_site, created_q_site) = QSite.objects.get_or_create(site=instance)
        except ProgrammingError:
            if instance.pk == 1:
                # this might fail during initial migration b/c the full set of db tables will not have been setup yet
                print("skipped creating site profile for %s" % (instance))
                pass
            else:
                msg = "Unable to create site profile for %s" % (instance)
                raise QError(msg)

post_save.connect(post_save_site_handler, sender=Site, dispatch_uid="post_save_site_handler")
