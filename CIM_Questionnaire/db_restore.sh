#!/bin/bash

##########################
# script to restore a db #
##########################

#########
# usage #
#########

USAGE="Usage: `basename $0` [-v <full path to virtualenv>] -f <path to backup file>"

####################
# global variables #
####################

SCRIPT="`pwd`/db_restore.py"
CURRENT_VIRTUALENV=`basename $VIRTUAL_ENV 2>/dev/null`
REQUIRED_VIRTUALENV=""
BACKUP_FILE=""

###############
# get options #
###############

while getopts v:f: OPT; do
  case $OPT in
   v) REQUIRED_VIRTUALENV=$OPTARG
      ;;
   f) BACKUP_FILE=$OPTARG
      ;;
   *) echo $USAGE>&2; 
      exit;;
  esac
done

#################
# check options #
#################

# is there a restore script to run...
if [ ! -f "$SCRIPT" ]; then
  echo -e "unable to run `basename $0` due to inability to locate restore script: $SCRIPT">&2;
  exit;
fi

# is there a backup file to restore..
if [ -z "$BACKUP_FILE" ]; then
  echo $USAGE>&2;
  exit;
fi
if [ ! -e $BACKUP_FILE ]; then
  echo -e "unable to run `basename $0` due to inability to locate backup file: $BACKUP_FILE">&2;
  exit;
fi

# was a virtualenv specified...
if [ -n "$REQUIRED_VIRTUALENV" ]; then

  if [ ! -d "$REQUIRED_VIRTUALENV" ]; then
    echo -e "unable to run `basename $0` due to inability to locate virtualenv: $REQUIRED_VIRTUALENV">&2;
    exit;

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
    echo -e "unable to run `basename $0` due to invalid virtualenv">&2;
    exit;

  else
    echo -e "running w/ the $CURRENT_VIRTUALENV Python environemnt\n"
  fi

else
  echo -e "running w/ the default Python environemnt\n"

fi

############
# do stuff #
############

while true; do
    read -p "This script will delete the existing db contents.  Do you wish to continue? " input
    case $input in
        [Yy]* ) echo "yes"; break;;
        [Nn]* ) echo "no";  exit;;
        [Cc]*|[Xx]*|[Qq]* ) exit;;
        * ) echo "Please choose a valid option.";;
    esac
done

SCRIPT_OUTPUT=`python $SCRIPT -f $BACKUP_FILE 2>&1`
echo -e "Output of `basename $SCRIPT`:\n$SCRIPT_OUTPUT"

###########
# the end #
###########
