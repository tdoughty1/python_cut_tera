#!/usr/local/anaconda/bin/python
'''
This script schedules the cuts to be re-made every few hours, but
only executes the script if it is no longer running.
'''
import sys
import time

from make_cuts_classy import rootcut

from apscheduler.scheduler import Scheduler

# Start the scheduler
sched = Scheduler()
sched.start()

@sched.interval_schedule(hours=6)
def job_func():
    t1 = time.time()
    rc = rootcut()
    rc.run_type_list = ['cf', 'ba', 'bg_lt_permitted']
    sys.stdout = open(rc.root_cutdir_gen + '/.log/' + rc.ttime + 'PythonDump.log', 'a')
    try:
        rc.main()
        t2 = time.time()
        print 'Build finished in {} s'.format(t2-t1)
    finally:
        sys.stdout.close()

