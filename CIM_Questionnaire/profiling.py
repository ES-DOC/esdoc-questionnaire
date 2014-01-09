
####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Oct 1, 2013 10:48:30 AM"

"""
.. module:: profiling

Summary of module goes here

"""

import hotshot
import hotshot.stats

import os
import time
import settings
import tempfile

from functools import wraps

try:
    PROFILE_LOG_BASE = settings.PROFILE_LOG_BASE[0] # rel gives a tuple
except:
    PROFILE_LOG_BASE = tempfile.gettempdir()

def encode_profile(log_file):
    """Profile some callable.

    This decorator uses the hotshot profiler to profile some callable (like
    a view function or method) and dumps the profile data somewhere sensible
    for later processing and examination.

    It takes one argument, the profile log name. If it's a relative path, it
    places it under the PROFILE_LOG_BASE. It also inserts a time stamp into the
    file name, such that 'my_view.prof' become 'my_view_2010-02-11-T170321.prof',
    where the time stamp is in UTC. This makes it easy to run and compare
    multiple trials.
    """

    if not os.path.isabs(log_file):
        log_file = os.path.join(PROFILE_LOG_BASE, log_file)


    def _outer(f):
        def _inner(*args, **kwargs):
            # Add a timestamp to the profile output when the callable
            # is actually called.
            (base, ext) = os.path.splitext(log_file)
            base = base + "_" + time.strftime("%Y-%m-%d-T%H%M%S", time.gmtime())
            final_log_file = base + ext

            prof = hotshot.Profile(final_log_file)
            try:
                ret = prof.runcall(f, *args, **kwargs)
            finally:
                prof.close()
            print "created profile: %s" % final_log_file
            return ret

        # only profile in DEBUG mode
        if settings.PROFILE and settings.DEBUG:
            return _inner
        else:
            return f

    return _outer


def decode_profile(profile):
    stats = hotshot.stats.load(profile)
    #stats.strip_dirs()
    stats.sort_stats('time', 'calls')
    stats.print_stats(20)


###############################
# memory profiling            #
###############################

from guppy  import hpy
hpy = hpy()
#SETUP_HPY = False  # defined in settings.py

def setup_hpy(reset=False):
    print "setting up heapy..."
    if (not settings.SETUP_HPY) or (reset) :
        print "resetting it"
        hpy.setrelheap()
        settings.SETUP_HPY = True
    else:
        print "not resetting it"

def profile_memory(log_file):

    if not os.path.isabs(log_file):
        log_file = os.path.join(PROFILE_LOG_BASE, log_file)

    def _outer(fn):
        def _inner(request, *args, **kwargs):

            # only profile in DEBUG mode
            if settings.PROFILE and settings.DEBUG:
                # before fn call...
                (base, ext) = os.path.splitext(log_file)
#                base = base + "_" + time.strftime("%Y-%m-%d-T%H%M%S", time.gmtime())
                final_log_file = base + ext
                setup_hpy()

            # fn call..
            retval = fn(request, *args, **kwargs)

            if settings.PROFILE and settings.DEBUG:
                # after fn call...
                hp = hpy.heap()
                with open(final_log_file,'w') as f:
                    f.write(str(hp))
                f.closed

            return retval

        return wraps(fn)(_inner)

    return _outer