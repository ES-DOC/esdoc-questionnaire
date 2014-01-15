#! /usr/bin/python

__author__="allyn.treshansky"
__date__ ="$Jan 15, 2014 15:28:06 PM$"

import os
import datetime

from subprocess     import call
from django.conf    import settings

rel = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

TIMESTAMP   = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
BACKUP_DIR  = rel('backups/')

if __name__ == "__main__":

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    DATABASE    = settings.DATABASES["default"]

    ENGINE      = DATABASE["ENGINE"]
    NAME        = DATABASE["NAME"]
    HOST        = DATABASE["HOST"]
    USER        = DATABASE["USER"]
    PASSWORD    = DATABASE["PASSWORD"]
    PORT        = DATABASE["PORT"]

    if "psycopg" in ENGINE:
        print "backing up a postgres db..."

        BACKUP_FILE     = "%sbackup_%s_%s.sql.tgz" % (BACKUP_DIR,NAME,TIMESTAMP)
        BACKUP_COMMAND  = "/usr/bin/pg_dump"
        BACKUP_ARGS     = ["-Ft","-v","-b","-c","-O","-f%s"%(BACKUP_FILE),NAME]

    elif "sqlite" in ENGINE:
        print "backing up a sqlite db..."
        msg = "you don't need a fancy script to backup sqlite; just copy the file"
        raise Exception(msg)

    elif "mysql" in ENGINE:

        print "backing up a mysql db..."
        msg = "this script cannot handle mysql yet"
        raise Exception(msg)

    else:

        msg = "unkown db type '%s'; aborting" % (ENGINE)
        raise Exception(msg)


    BACKUP_ARGS.insert(0,BACKUP_COMMAND)
    call(BACKUP_ARGS)
