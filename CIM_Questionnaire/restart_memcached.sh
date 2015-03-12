#!/bin/bash

#########################################################
# script to start memcached if it's not already running #
#########################################################

#########
# usage #
#########

USAGE="Usage: `basename $0` [-h <host name>] [-p <port number>]"

####################
# global variables #
####################

HOST="127.0.0.1"  # default localhost
PORT="11211"  # default memcached port
MEMORY="128"  # MB of memory to use (default is 64)

###############
# get options #
###############

while getopts h:p: OPT; do
  case $OPT in
    h) HOST="$OPTARG";;
    p) PORT="$OPTARG";;
    *) echo $USAGE>&2; 
       exit;;
  esac
done;

############
# do stuff #
############

if ps -U $USER | grep memcached > /dev/null; then
  echo "memcached is running"
else
  echo "memcached is not running... restarting..."
  memcached -l $HOST -p $PORT -d -m 128
fi

