#!/usr/bin/env python
import os
import sys
import tempfile
import time

log_file = "cim_questionnaire_memory_profile.log"

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    
    from django.core.management import execute_from_command_line
    import settings

    # memory profiling...
    if settings.PROFILE and settings.DEBUG:
        from guppy  import hpy
        try:
            PROFILE_LOG_BASE = settings.PROFILE_LOG_BASE[0] # rel gives a tuple
        except:
            PROFILE_LOG_BASE = tempfile.gettempdir()
        if not os.path.isabs(log_file):
            log_file = os.path.join(PROFILE_LOG_BASE, log_file)
        (base, ext) = os.path.splitext(log_file)
        base = base + "_" + time.strftime("%Y-%m-%d-T%H%M%S", time.gmtime())
        final_log_file = base + ext
        hpy = hpy()
        hpy.setrelheap()

    execute_from_command_line(sys.argv)

    # memory profiling...
    if settings.PROFILE and settings.DEBUG:
        hp = hpy.heap()
        with open(final_log_file,'w') as f:
            f.write(str(hp))
            f.closed
