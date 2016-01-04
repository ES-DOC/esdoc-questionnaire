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
script for restoring the Q database based on a file created w/ "db_backup.py"
THIS IS A DESTRUCTIVE SCRIPT; IT WILL OVERWRITE THE EXISTING DB
(run w/in virtualenv as needed)
"""

# get Django loaded...

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Q.settings")

# now load other stuff...

import argparse
import tempfile
from django.conf import settings
from subprocess import call, check_call, CalledProcessError
from Q.questionnaire.q_utils import QError

# get args...

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', help='backup file to restore', required=True)
args = vars(parser.parse_args())

restore_file = args["file"]

if not os.path.isfile(restore_file):
    msg = "unable to locate '{0}'".format(restore_file)
    raise QError(msg)

# get db details...

try:
    db_conf = settings.DATABASES["default"]
except KeyError:
    msg = "unable to find valid database configuration"
    raise QError(msg)
db_backend = db_conf.get("ENGINE")

# figure out the cmds for restoring the specific db...

if 'postgres' in db_backend:

    print("restoring a postgres db...")

    restore_cmd = "/usr/bin/pg_restore"

    # pg_restore may fail when trying to re-create the _entire_ db b/c of issues w/ "plpgsql" tables
    # this is a known issue [http://www.postgresql.org/message-id/201110220712.30886.adrian.klaver@gmail.com]
    # to fix it, I can remove the offending lines from the db dump as follows:
    # `pg_restore -l $BACKUP_FILE | grep -vi plpgsql > $TMPFILE`
    # and then run the same restore command as below w/ the addition of "-L $TMPFILE"
    # technically, this is a bad solution b/c of the "shell=True" argument
    # so, perhaps I should just ignore the errors (by never including the "-e" flag)
    (tmpfile, tmpfile_path) = tempfile.mkstemp(dir=os.getcwd())
    call(
        "{0} -l {1} | grep -vi plpgsql > {2}".format(restore_cmd, restore_file, tmpfile_path),
        shell=True
    )

    # note the use of "-O" which does not try to match ownership of the original backed-up db
    # (however, "-U -W" ensures users still must be authenticated against the db being changed)

    restore_args = [
        "-c",
        "-v",
        "-L{0}".format(tmpfile_path),
        "-d{0}".format(db_conf.get("NAME")),
        "-O",
        "-h{0}".format(db_conf.get("HOST")),
        "-p{0}".format(db_conf.get("PORT")),
        "-U{0}".format(db_conf.get("USER")),
        "-W",
        restore_file,
    ]

elif "sqlite" in db_backend:

    print("restoring a sqlite db...")
    msg = "you don't need a fancy script to restore sqlite; just copy the file"
    raise QError(msg)

elif "mysql" in db_backend:

    print("restoring a mysql db...")
    msg = "this script cannot handle mysql yet"
    raise QError(msg)

else:

    msg = "unknown db backend: '{0}'".format(db_backend)
    raise QError(msg)

restore_args.insert(0, restore_cmd)

# perform the actual restore...

try:
    check_call(restore_args)  # note, unlike the db_backup script, I do not pass an "env" argument b/c I do not have to deal w/ sensitive passwords b/c this script is meant to be run interactively
    msg = "successfully restored '{0}".format(restore_file)
    print(msg)
except OSError:
    msg = "unable to find {0}".format(restore_cmd)
    raise QError(msg)
except CalledProcessError as e:
    msg = "error restoring '{0}'".format(restore_file)
    print(msg)

# clean up the filesystem, just in-case...

try:
    os.unlink(tmpfile_path)
except:
    pass

# hooray, you're done
