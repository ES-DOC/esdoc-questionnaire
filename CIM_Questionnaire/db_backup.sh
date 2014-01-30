#!/bin/bash

# (an explicit reference to bash is required for the 'source' command to work)
# (some Ubuntu distributions symlink sh to 'dash')

##########################
# script to restore a db #
##########################

#########
# usage #
#########

USAGE="Usage: `basename $0` [-v <full path to virtualenv>] [-l <full path to logfile> (defaults to cwd/backups/logfile.txt)]"

####################
# global variables #
####################

TIMESTAMP="`date +%Y-%m-%d-%H%M`"
LOGFILE="`pwd`/backups/logfile.txt"
SCRIPT="`pwd`/db_backup.py"
CURRENT_VIRTUALENV=`basename $VIRTUAL_ENV 2>/dev/null`
REQUIRED_VIRTUALENV=""
MSG="\n--------------------\n$TIMESTAMP: running `basename $0` from `pwd`..."
ERROR=0

###############
# get options #
###############

while getopts v:l: OPT; do
  case $OPT in
    v) REQUIRED_VIRTUALENV="$OPTARG"
       ;;
    l) LOGFILE="$OPTARG"
       ;;
    *) echo $USAGE>&2; 
       exit;;
  esac
done;

#################
# check options #
#################

# is there a place to write output...
if [ ! -f $LOGFILE ]; then
  echo "unable to locate valid logfile">&2; 
  exit;
fi

# is there a backup script to run...
if [ ! -f "$SCRIPT" ]; then
  MSG="$MSG\n$TIMESTAMP: unable to run `basename $0` due to inability to locate backup script: $SCRIPT"
  ERROR=1
fi

# was a virtualenv specified...
if [ -n "$REQUIRED_VIRTUALENV" ]; then

  if [ ! -d "$REQUIRED_VIRTUALENV" ]; then
    MSG="$MSG\n$TIMESTAMP: unable to run `basename $0` due to inability to locate virtualenv: $REQUIRED_VIRTUALENV"
    ERROR=1

  else
    # is there currently a virtualenv running...
    # if not, can we start the required one...
    if [ -z "$CURRENT_VIRTUALENV" ]; then
      source "$REQUIRED_VIRTUALENV/bin/activate"
      CURRENT_VIRTUALENV=`basename $VIRTUAL_ENV 2>/dev/null`
    fi
  fi

  # is the correct virtualenv running...
  if [ "`basename $REQUIRED_VIRTUALENV`" != "$CURRENT_VIRTUALENV" ]; then
    MSG="$MSG\n$TIMESTAMP: unable to run `basename $0` due to invalid virtualenv"
    ERROR=1

  else
    MSG="$MSG\n$TIMESTAMP: running w/ the $CURRENT_VIRTUALENV python environment"
  fi

else

  if [ -z "$CURRENT_VIRTUALENV" ]; then
    MSG="$MSG\n$TIMESTAMP: running w/ the default python environment"
  else
    MSG="$MSG\n$TIMESTAMP: running w/ the $CURRENT_VIRTUALENV python environment"
  fi

fi

############
# do stuff #
############

# quit if any of the above checks failed...
if [ $ERROR -eq 1 ]; then

  echo -e $MSG>>$LOGFILE
  echo -e $MSG

# otherwise run the script and write the output...
else

  SCRIPT_OUTPUT=`python $SCRIPT`
  MSG="$MSG\nScript Output: $SCRIPT_OUTPUT"
  echo -e $MSG>>$LOGFILE
  echo -e $MSG

fi
