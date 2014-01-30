#! /usr/bin/python

__author__="allyn.treshansky"
__date__ ="$Jan 15, 2014 15:28:06 PM$"

import os
import argparse

from subprocess     import call, check_call, CalledProcessError
from django.conf    import settings

if __name__ == "__main__":

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    try:
        DATABASE    = settings.DATABASES["default"]
    except KeyError:
        msg = "unable to find valid database configuration"
        raise Exception(msg)

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
        #
        # note the use of "-O" which does not try to match ownership of the original backed-up db        
        # (however, "-h -U -W" ensures users still must be authenticated against the db being changed)
        #
        RESTORE_ARGS     = ["-c","-v","-d%s"%(NAME),"-O","-h%s"%(HOST),"-U%s"%(USER),"-W",RESTORE_FILE]

        #RESTORE_ARGS     = ["-c","-v","-d%s"%(NAME),"-U%s"%(USER),"-W",RESTORE_FILE]
        #RESTORE_ARGS     = ["-c","-v","-d%s"%(NAME),"-W",RESTORE_FILE]

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

    try:
        check_call(RESTORE_ARGS)
        print "succesfully restored %s" % (RESTORE_FILE)
    except OSError:
        msg = "unable to find %s" % (RESTORE_COMMAND)
        print msg
        raise Exception(msg)
    except CalledProcessError:
        print "error"
        pass # handle errors in the called executable
