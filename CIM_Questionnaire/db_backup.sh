#!/bin/sh

##########################
# script to restore a db #
##########################

#########
# usage #
#########

USAGE="Usage: `basename $0`"

###############
# get options #
###############

if [ $# -ne 0 ]; then
  echo $USAGE >&2
  exit
fi

############
# do stuff #
############

python manage.py dbbackup -v 3 --compress

###########
# the end #
###########
