#! /usr/bin/python

__author__="allyn.treshansky"
__date__ ="$Jan 15, 2014 15:28:06 PM$"

import os
import argparse
import tempfile

from subprocess     import call, check_call, CalledProcessError
from django.conf    import settings

if __name__ == "__main__":

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    # unlike the backup script, I am not dealing w/ passwords; this is meant to be run interactively

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
        print "restoring a postgres db..."

        RESTORE_COMMAND  = "/usr/bin/pg_restore"

        # pg_restore may fail when trying to re-create the _entire_ db b/c of issues w/ "plpgsql" tables
        # this is a known issue [http://www.postgresql.org/message-id/201110220712.30886.adrian.klaver@gmail.com]
        # to fix it, I can remove the offending lines from the db dump as follows:
        # `pg_restore -l $BACKUP_FILE | grep -vi plpgsql > $TMPFILE`
        # and then run the same restore command as below w/ the addition of "-L $TMPFILE"
        # technically, this is a bad solution b/c of the "shell=True" argument
        # so, perhaps I should just ignore the errors (by not including the "-e" flag)
        (tmpfile,tmpfile_path) = tempfile.mkstemp(dir=os.getcwd())
        call("%s -l %s | grep -vi plpgsql > %s"%(RESTORE_COMMAND,RESTORE_FILE,tmpfile_path),shell=True)

        #
        # note the use of "-O" which does not try to match ownership of the original backed-up db        
        # (however, "-U -W" ensures users still must be authenticated against the db being changed)
        #
        RESTORE_ARGS     = ["-e","-c","-v","-L%s"%(tmpfile_path),"-d%s"%(NAME),"-O","-h%s"%(HOST),"-p%s"%(PORT),"-U%s"%(USER),"-W",RESTORE_FILE]
        #RESTORE_ARGS     = ["-c","-v","-d%s"%(NAME),"-O","-h%s"%(HOST),"-p%s"%(PORT),"-U%s"%(USER),"-W",RESTORE_FILE]
        #RESTORE_ARGS     = ["-c","-v","-d%s"%(NAME),"-U%s"%(USER),"-W",RESTORE_FILE]
        #RESTORE_ARGS     = ["-c","-v","-d%s"%(NAME),"-W",RESTORE_FILE]
     
    elif "sqlite" in ENGINE:
        print "restoring a sqlite db..."
        msg = "you don't need a fancy script to restore sqlite; just copy the file"
        raise Exception(msg)

    elif "mysql" in ENGINE:

        print "restoring a mysql db..."
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

    # if I had to touch the filesystem,
    # be sure to clean up...
    try:
        #tmpfile.close()
        os.unlink(tmpfile_path)
    except:
        pass