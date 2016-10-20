####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from functools import wraps
from django.shortcuts import redirect
from Q.questionnaire.models.models_projects import QProject

__author__ = 'allyn.treshansky'

LEGACY_HOST = "questionnaire.es-doc.org"


def redirect_legacy_projects(view_fn):
    """
    Decorator that redirects a view to the legacy site
    if the project being viewed is a legacy project.
    The legacy site has a codebase that supports CIM1;
    It is frozen at v0.15.1.0.
    """

    @wraps(view_fn)
    def wrapper(*args, **kwargs):
        request = args[0]
        if request.method == "GET" and not request.is_ajax():
            # only process if this is a normal "GET"
            # (that's the 1st time the view would have been called)
            project_name = kwargs.get("project_name")
            if project_name:
                try:
                    project = QProject.objects.get(name=project_name)
                    if project.is_legacy:
                        legacy_url = request.build_absolute_uri().replace(
                            request.get_host(),
                            LEGACY_HOST
                        )
                        return redirect(legacy_url, permanent=True)
                except QProject.DoesNotExist:
                    pass
        return view_fn(*args, **kwargs)

    return wrapper
