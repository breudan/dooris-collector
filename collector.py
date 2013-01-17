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
output = {'apiversion': 1}

def fetch_doorstatus():
    """Read door status via SSH to Raspi."""
    shell = spur.SshShell(hostname=CONFIG.get('door', 'sshhost'),
                          username=CONFIG.get('door', 'sshuser'),
                          port=int(CONFIG.get('door', 'sshport')),
                          private_key_file=CONFIG.get('door', 'sshkey'))
    doorstatus = shell.run(['cat', '/sys/class/gpio/gpio0/value']).output
    doorstatus = doorstatus.strip()
    now = datetime.datetime.now().strftime('%s')
    # TODO error handling
    if not output.has_key('door'):
        output['door'] = {'status': '-1'}
    if output['door']['status'] != doorstatus:
        output['door']['status'] = doorstatus
        output['door']['last_change'] = now
    output['door']['last_update'] = now


def fetch_routerstatus():
    """Read router status via SSH to router."""
    shell = spur.SshShell(hostname=CONFIG.get('router', 'sshhost'),
                          username=CONFIG.get('router', 'sshuser'),
                          port=int(CONFIG.get('router', 'sshport')),
                          private_key_file=CONFIG.get('router', 'sshkey'))
    dhcpclients = shell.run(['wc', '-l', '/tmp/dhcp.leases']).output
    dhcpclients = dhcpclients.split()[0].strip()
    now = datetime.datetime.now().strftime('%s')
    # TODO error handling
    if not output.has_key('router'):
        output['router'] = {'dhcp': '-1'}
    if output['router']['dhcp'] != dhcpclients:
        output['router']['dhcp'] = dhcpclients
        output['router']['last_change'] = now
    output['router']['last_update'] = now


def write_output():
    """Collect data and write output files."""
    fetch_doorstatus()
    fetch_routerstatus()

    with open('schema.json', 'r') as schf:
        schema = json.load(schf)
        try:
            jsonschema.validate(output, schema)
            with open(CONFIG.get('general', 'jsonoutputfile'), 'w') as jof:
                jof.write('{0}\n'.format(json.dumps(output)))
        except jsonschema.ValidationError, jsonschema.SchemaError:
            print json.dumps(output)
            print "Malformed JSON generated."


if __name__ == "__main__":
    SCHED = Scheduler()
    SCHED.start()
    SCHED.add_interval_job(write_output, minutes=2)

    while True:
        time.sleep(500)
