#!/bin/bash

#########################################################
# script to start memcached if it's not already running #
#########################################################

#########
# usage #
#########

USAGE="Usage: `basename $0` [-h <host name>] [-p <port number>] [-v (verbose)]"

####################
# global variables #
####################

HOST="127.0.0.1"  # default localhost
PORT="11211"  # default memcached port
MEMORY="128"  # MB of memory to use (default is 64)

###########
# logging #
###########

VERBOSE=0  

function log() {
  if [[ $VERBOSE -eq 1 ]]; then
    echo "$@"
  fi
}

###############
# get options #
###############

while getopts h:p:v OPT; do
  case $OPT in
    h) HOST="$OPTARG";;
    p) PORT="$OPTARG";;
    v) VERBOSE=1;;
    *) echo $USAGE>&2; 
       exit;;
  esac
done;

############
# do stuff #
############

memcached_running=`ps -e | grep memcached 2>/dev/null`

if [ ! -z "$memcached_running" ]; then
  log "memcached is running"
else
  log "memcached is not running... restarting..."
  memcached -l $HOST -p $PORT -d -m 128
fi

