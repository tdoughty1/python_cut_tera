#!/usr/local/anaconda/bin/python
'''
This script schedules the cuts to be re-made every few hours, but
only executes the script if it is no longer running.
'''
import sys
import time
import smtplib
import textwrap

def sendemail(from_addr, to_addr_list, cc_addr_list,
              subject, message,
              login, password,
              smtpserver='smtp.gmail.com:587'):
    header  = 'From: %s\n' % from_addr
    header += 'To: %s\n' % ','.join(to_addr_list)
    header += 'Cc: %s\n' % ','.join(cc_addr_list)
    header += 'Subject: %s\n\n' % subject
    message = header + message

    server = smtplib.SMTP(smtpserver)
    server.starttls()
    server.login(login,password)
    problems = server.sendmail(from_addr, to_addr_list, message)
    server.quit()
    return problems

def excepter(e):
    message = textwrap.dedent("""\

            There has been an error with the automated cut production!
            The exception message is:

            {}

            please connect to production@cdmstera2 and debug.
            for documentation please see https://github.com/durcan/python_cut_tera""".format(e))
    sendemail(from_addr    = 'cdms.production@gmail.com',
            to_addr_list = ['serfass@berkeley.edu'],
            cc_addr_list = ['cornell@caltech.edu'],
            subject      = 'Cut production error!',
            message      = message,
            login        = 'cdms.production@gmail.com',
            password     = 'SoupRcdms')
if __name__ == '__main__':
    from make_cuts_classy import rootcut

    from apscheduler.scheduler import Scheduler

    # Start the scheduler
    sched = Scheduler()
    sched.start()

    @sched.interval_schedule(hours=4)
    def job_func():
        try:
            t1 = time.time()
            rc = rootcut()
            rc.run_type_list = ['cf', 'ba', 'bg_lt_permitted']
            sys.stdout = open(rc.root_cutdir_gen + '/.log/' + rc.ttime + 'PythonDump.log', 'a')
            try:
                rc.main()
                t2 = time.time()
                print 'Build finished in {} s'.format(t2-t1)
            except Exception as e:
                excepter(e)
            finally:
                sys.stdout.close()
        except Exception as e2:
            excepter(e2)

    while True:
        x = raw_input('Type "kill" to terminate. Any other input returns info.')
        if x == 'kill':
            sched.shutdown()
            break
        else:
            sched.print_jobs()
