####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

"""
script for backing up the Q database to file
(run w/in virtualenv as needed)
"""

# get Django loaded...

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Q.settings")

# now load other stuff...

import datetime
from django.conf import settings
from subprocess import check_call, CalledProcessError
from Q.questionnaire.q_utils import rel, QError

# global variables...

ENV = os.environ.copy()  # work on a copy ENV in-case I can't or don't want to change global settings
TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
BACKUP_DIR = rel('../backups/')

# get db details...

try:
    db_conf = settings.DATABASES["default"]
except KeyError:
    msg = "unable to find valid database configuration"
    raise QError(msg)
db_backend = db_conf.get("ENGINE")

# figure out the cmds for backing up the specific db...

if 'postgres' in db_backend:

    print("backing up a postgres db...")

    backup_file = os.path.join(BACKUP_DIR, "backup_{0}_{1}.sql.tgz".format(db_conf.get("NAME"), TIMESTAMP))
    backup_cmd = "/usr/bin/pg_dump"

    # note the use of "-O" which does not constrain table ownership
    # however, the docs of pg_dump state:
    #  <snip>
    #  This option is only meaningful for the plain-text format.
    #  For the archive formats, you can specify the option when you call pg_restore.
    #  </snip>

    backup_args = [
        "-Ft",
        "-v",
        "-b",
        "-c",
        "-O",
        "-h{0}".format(db_conf.get("HOST")),
        "-p{0}".format(db_conf.get("PORT")),
        "-U{0}".format(db_conf.get("USER")),
        "-w",
        "-f{0}".format(backup_file),
        db_conf.get("NAME"),
    ]

    ENV["PGPASSWORD"] = db_conf.get("PASSWORD")  # bypass manually inputting pwd by using '-w' flag w/ an ENV variable

elif "sqlite" in db_backend:

    print("backing up a sqlite db...")
    msg = "you don't need a fancy script to backup sqlite; just copy the file"
    raise QError(msg)

elif "mysql" in db_backend:

    print("backing up a mysql db...")
    msg = "this script cannot handle mysql yet"
    raise QError(msg)

else:

    msg = "unknown db backend: '{0}'".format(db_backend)
    raise QError(msg)

backup_args.insert(0, backup_cmd)

# open the logfile and perform the actual backup...

with open(os.path.join(BACKUP_DIR, "log.txt"), 'a') as log_file:

    try:
        check_call(backup_args, env=ENV)
        msg = "successfully created '{0}'".format(backup_file)
        print(msg)
        log_file.write("{0}: {1}\n".format(TIMESTAMP, msg))
    except OSError:
        msg = "unable to find {0}".format(backup_cmd)
        raise QError(msg)
    except CalledProcessError as e:
        msg = "error creating '{0}'".format(backup_file)
        print(msg)
        log_file.write("{0}: {1}\n".format(TIMESTAMP, msg))

# clean up...

log_file.closed

# hooray, you're done
