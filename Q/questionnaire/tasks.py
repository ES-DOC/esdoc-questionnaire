from celery import shared_task
from django.core.management import call_command
from django.db.models import get_app, get_models

import datetime
import json
import os

from Q.questionnaire import APP_LABEL
from Q.questionnaire.models import *
from Q.questionnaire.q_utils import rel

BACKUP_DIR = rel('../backups/')
BACKUP_PREFIX = "celery_backup"
BACKUP_EXTENT = 30  # assuming I am doing a daily backup, this will keep about a month's worth of backups on disk


# there is a particular order that objects ought to be serialized in...

q_models_to_order = [
    QInstitute,
    QSite,
    QUserProfile,
    QOntology,
    QProject,
    QProjectOntology,
    QSynchronization,
]

# explicitly get any Users & Sites 1st...
# then get ordered models from the questionnaire...
# then get remaining models from the questionnaire...
ordered_models = ["auth.user", "sites.site", ] + \
    [m._meta.db_table.replace('_', '.') for m in q_models_to_order] + \
    [m._meta.db_table.replace('_', '.') for m in get_models(get_app(APP_LABEL)) if m not in q_models_to_order]


def get_sorted_fixtures():
    """
    returns a list of full pathnames for existing fixture files sorted by creation time
    :return:
    """
    fixtures = [
        os.path.join(BACKUP_DIR, f)
        for f in os.listdir(BACKUP_DIR) if f.startswith(BACKUP_PREFIX)
    ]
    sorted_fixtures = sorted(fixtures, key=lambda sf: os.path.getctime(sf))
    return sorted_fixtures


@shared_task
def create_fixtures():
    """
    create a new fixture if the db has changed
    :return:
    """
    # create fixtures based on the current db state...
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    fixture_filename = os.path.join(BACKUP_DIR, "{0}_{1}.json".format(BACKUP_PREFIX, timestamp))
    call_command("dumpdata", args=ordered_models, format="json", indent=4, output=fixture_filename)

    # but immediately delete those fixtures if they aren't any different from the last time this fn ran...
    fixtures = get_sorted_fixtures()
    try:
        with open(fixtures[-1], "r") as f1:
            newest_fixtures = json.load(f1)
        f1.closed
        with open(fixtures[-2], "r") as f2:
            next_newest_fixtures = json.load(f2)
        f2.closed
        if newest_fixtures == next_newest_fixtures:
            os.remove(fixture_filename)
    except IndexError:
        pass


@shared_task
def cull_fixtures():
    """
    only keep BACKUP_EXTENT fixtures at any given time; delete all older ones
    :return:
    """

    fixtures = get_sorted_fixtures()
    n_fixtures = len(fixtures)
    if n_fixtures > BACKUP_EXTENT:
        for f in fixtures[:n_fixtures - BACKUP_EXTENT]:
            os.remove(f)
