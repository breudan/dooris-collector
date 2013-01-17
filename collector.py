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
import jsonschema
from apscheduler.scheduler import Scheduler

CONFIG = ConfigParser.SafeConfigParser()
CONFIG.read('dooris.cfg')


def fetch_doorstatus():
    """Read door status via SSH to Raspi."""
    shell = spur.SshShell(hostname=CONFIG.get('door', 'sshhost'),
                          username=CONFIG.get('door', 'sshuser'),
                          port=CONFIG.get('router', 'sshport'),
                          private_key_file=CONFIG.get('door', 'sshkey'))
    doorstatus = shell.run(['cat', '/sys/class/gpio/gpio0/value'])
    # TODO error handling
    return doorstatus.output.strip()


def fetch_routerstatus():
    """Read router status via SSH to router."""
    shell = spur.SshShell(hostname=CONFIG.get('router', 'sshhost'),
                          username=CONFIG.get('router', 'sshuser'),
                          port=CONFIG.get('router', 'sshport'),
                          private_key_file=CONFIG.get('router', 'sshkey'))
    dhcpclients = shell.run(['wc', '-l', '<', '/tmp/dhcp.leases'])
    # TODO error handling
    return dhcpclients.output.strip()


def write_output():
    """Collect data and write output files."""
    result = {'door': {'status': fetch_doorstatus(),
                       'last_change': '0',  # TODO calculate last change
                       'last_update': datetime.datetime.now().strftime('%s')},
              'router': {'status': fetch_routerstatus(),
                         'last_change': '0',
                         'last_update': datetime.datetime.now().strftime('%s')},
              'apiversion': 0.1}

    with open('schema.json', 'r') as schf:
        schema = json.load(schf)
        try:
            jsonschema.validate(result, schema)
            with open(CONFIG.get('general', 'jsonoutputfile'), 'w') as jof:
                jof.write('{0}\n'.format(json.dumps(result)))
        except jsonschema.ValidationError, jsonschema.SchemaError:
            print "Malformed JSON generated."


if __name__ == "__main__":
    SCHED = Scheduler()
    SCHED.start()
    SCHED.add_interval_job(write_output, minutes=2)

    while True:
        time.sleep(500)
