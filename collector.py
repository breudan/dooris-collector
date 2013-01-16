# -*- coding: utf-8 -*-
"""
    Dooris Collector
    ================

    Collects data from various Dooris sensors, conditions them,
    and makes them available for different 3rd party tools.

    :copyright: (c) 2013 Christoph Gebhardt
    :license: BSD, see LICENSE for details
"""
import spur
import ConfigParser
import datetime
import time
from apscheduler.scheduler import Scheduler

CONFIG = ConfigParser.SafeConfigParser()
CONFIG.read('dooris.cfg')


def getdoorstatus():
    """
    Read door status via SSH to Raspi.
    """
    shell = spur.SshShell(hostname=CONFIG.get('door', 'sshhost'),
                        username=CONFIG.get('door', 'sshuser'),
                        private_key_file=CONFIG.get('door', 'sshkey'))
    doorstatus = shell.run(['cat', '/sys/class/gpio/gpio0/value'])
    print 'door is closed' if doorstatus.output else 'door is open'
    return doorstatus.output


def writeoutput():
    """
    Write output files.
    """
    with open(CONFIG.get('general', 'classicoutputfile'), 'w') as cof:
        cof.write(getdoorstatus())
        cof.write('{}\n'.format(datetime.datetime.now().strftime('%s')))


if __name__ == "__main__":
    SCHED = Scheduler()
    SCHED.start()
    SCHED.add_interval_job(writeoutput, seconds=20)

    while True:
        time.sleep(60)
