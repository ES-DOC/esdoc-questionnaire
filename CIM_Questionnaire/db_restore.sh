#!/bin/sh

##########################
# script to restore a db #
##########################

#########
# usage #
#########

USAGE="Usage: `basename $0` -f <backup file>"

####################
# global variables #
####################

BACKUP_FILE=""

###############
# get options #
###############

if [ $# -ne 2 ]; then
  echo $USAGE >&2
  exit
fi

while getopts f: OPT
do
  case $OPT in
    f) BACKUP_FILE=$OPTARG;
       shift;;
    *) echo $USAGE >&2; 
       exit;;
  esac
done;

if [ ! -e $BACKUP_FILE ]; then
  echo "cannot locate $BACKUP_FILE">&2;
  exit
fi


while true; do
    read -p "This script will delete the existing db contents.  Do you wish to continue? " input
    case $input in
        [Yy]* ) echo "yes"; break;;
        [Nn]* ) echo "no";  exit;;
        [Cc]*|[Xx]*|[Qq]* ) exit;;
        * ) echo "Please choose a valid option.";;
    esac
done

############
# do stuff #
############

python manage.py dbrestore -v 3 -f $BACKUP_FILE

###########
# the end #
###########
