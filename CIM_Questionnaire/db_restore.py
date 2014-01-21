#! /usr/bin/python

__author__="allyn.treshansky"
__date__ ="$Jan 15, 2014 15:28:06 PM$"

import os
import argparse

from subprocess     import call
from django.conf    import settings

#rel = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

if __name__ == "__main__":

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    DATABASE    = settings.DATABASES["default"]

    ENGINE      = DATABASE["ENGINE"]
    NAME        = DATABASE["NAME"]
    HOST        = DATABASE["HOST"]
    USER        = DATABASE["USER"]
    PASSWORD    = DATABASE["PASSWORD"]
    PORT        = DATABASE["PORT"]

    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--file', help='backup file to restore', required=True)
    args = vars(parser.parse_args())

    RESTORE_FILE = args["file"]

    if not os.path.isfile(RESTORE_FILE):
        msg = "unable to locate %s" % (RESTORE_FILE)
        raise Exception(msg)

    if "psycopg" in ENGINE:
        print "restoring up a postgres db..."

        RESTORE_COMMAND  = "/usr/bin/pg_restore"
        RESTORE_ARGS     = ["-c","-v","-d%s"%(NAME),"-U%s"%(USER),"-W",RESTORE_FILE]

    elif "sqlite" in ENGINE:
        print "restoring up a sqlite db..."
        msg = "you don't need a fancy script to restore sqlite; just copy the file"
        raise Exception(msg)

    elif "mysql" in ENGINE:

        print "restoring up a mysql db..."
        msg = "this script cannot handle mysql yet"
        raise Exception(msg)

    else:

        msg = "unkown db type '%s'; aborting" % (ENGINE)
        raise Exception(msg)


    RESTORE_ARGS.insert(0,RESTORE_COMMAND)
    call(RESTORE_ARGS)
