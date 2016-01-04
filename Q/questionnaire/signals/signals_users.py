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

from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models import User

from Q.questionnaire.models.models_users import QUserProfile


def post_save_user_handler(sender, **kwargs):
    """
    fn that gets called after a standard Django User is saved;
    if it's just been created, then the corresponding QUserProfile needs to be setup
    :param sender:
    :param kwargs:
    :return:
    """
    created = kwargs.pop("created", True)
    user = kwargs.pop("instance", None)
    if user and created:
        QUserProfile.objects.create(user=user)


post_save.connect(post_save_user_handler, sender=User, dispatch_uid="post_save_user_handler")


def post_delete_profile_handler(sender, **kwargs):
    """
    fn that gets called after a QUserProfile is deleted;
    When a standard Django User is deleted, the corresponding QUserProfile will also be deleted (b/c of the 1-to-1 relationship)
    but if a QUserProfile is explicitly deleted, this fn ensures that the corresponding User is deleted
    :param sender:
    :param kwargs:
    :return:
    """
    profile = kwargs.pop("instance", None)
    if profile:
        user = profile.user
        if user:
            user.delete()

post_delete.connect(post_delete_profile_handler, sender=QUserProfile, dispatch_uid="post_delete_profile_handler")



