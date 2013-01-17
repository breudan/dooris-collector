# -*- coding: utf-8 -*-
""" Dooris Collector
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
import json
from apscheduler.scheduler import Scheduler

CONFIG = ConfigParser.SafeConfigParser()
CONFIG.read('dooris.cfg')


def fetch_doorstatus():
    """Read door status via SSH to Raspi."""
    shell = spur.SshShell(hostname=CONFIG.get('door', 'sshhost'),
                          username=CONFIG.get('door', 'sshuser'),
                          private_key_file=CONFIG.get('door', 'sshkey'))
    doorstatus = shell.run(['cat', '/sys/class/gpio/gpio0/value'])
    # TODO error handling
    return doorstatus.output.strip()


def write_output():
    """Collect data and write output files."""
    result = {'door': {'status': fetch_doorstatus(),
                       'last_change': '0',  # TODO calculate last change
                       'last_update': datetime.datetime.now().strftime('%s')},
              'apiversion': 0.1}

    with open(CONFIG.get('general', 'jsonoutputfile'), 'w') as jof:
        jof.write('{0}\n'.format(json.dumps(result)))


if __name__ == "__main__":
    SCHED = Scheduler()
    SCHED.start()
    SCHED.add_interval_job(write_output, minutes=2)

    while True:
        time.sleep(500)
