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
import daemon
from apscheduler.scheduler import Scheduler


class Collector:
    """Collects various Dooris sensor data and write output files"""

    def __init__(self):
        self.config = ConfigParser.SafeConfigParser()
        self.config.read('dooris.cfg')
        self.output = {'apiversion': 1}

    def fetch_doorstatus(self):
        """Read door status via SSH to Raspi."""
        shell = spur.SshShell(hostname=self.config.get('door', 'sshhost'),
                              username=self.config.get('door', 'sshuser'),
                              port=int(self.config.get('door', 'sshport')),
                              private_key_file=self.config.get('door',
                                                               'sshkey'))
        try:
            doorstatus = shell.run(['cat',
                                    '/sys/class/gpio/gpio0/value']).output
            doorstatus = doorstatus.strip()
        except:
            # no difference in misconfiguration and actual errors.
            # might need improvement. :)
            doorstatus = '-1'
        now = datetime.datetime.now().strftime('%s')
        if not 'door' in self.output:
            self.output['door'] = {'status': '-1'}
        if self.output['door']['status'] != doorstatus:
            self.output['door']['status'] = doorstatus
            self.output['door']['last_change'] = now
        self.output['door']['last_update'] = now

    def fetch_routerstatus(self):
        """Read router status via SSH to router."""
        shell = spur.SshShell(hostname=self.config.get('router', 'sshhost'),
                              username=self.config.get('router', 'sshuser'),
                              port=int(self.config.get('router', 'sshport')),
                              private_key_file=self.config.get('router',
                                                               'sshkey'))
        try:
            dhcpclients = shell.run(['wc', '-l', '/tmp/dhcp.leases']).output
            dhcpclients = dhcpclients.split()[0].strip()
        except:
            # no difference in misconfiguration and actual errors.
            # might need improvement. :)
            dhcpclients = '-1'
        now = datetime.datetime.now().strftime('%s')
        if not 'router' in self.output:
            self.output['router'] = {'dhcp': '-1'}
        if self.output['router']['dhcp'] != dhcpclients:
            self.output['router']['dhcp'] = dhcpclients
            self.output['router']['last_change'] = now
        self.output['router']['last_update'] = now

    def write_output(self):
        """Collect data and write output files."""
        with open('schema.json', 'r') as schf:
            schema = json.load(schf)
            try:
                jsonschema.validate(self.output, schema)
                with open(self.config.get('general', 'jsonoutputfile'),
                          'w') as jof:
                    jof.write('{0}\n'.format(json.dumps(self.output)))
            except jsonschema.ValidationError, jsonschema.SchemaError:
                print json.dumps(self.output)
                print "Malformed JSON generated."

    def collect_and_write(self):
        """collect each sensor, write each output"""
        self.fetch_doorstatus()
        self.fetch_routerstatus()
        self.write_output()


def runloop():
    """schedule collector task and loop forever"""
    sched = Scheduler()
    coll = Collector()
    sched.start()
    sched.add_interval_job(coll.collect_and_write, minutes=2)
    while True:
        time.sleep(500)

if __name__ == "__main__":
    with daemon.DaemonContext(working_directory='/home/seosamh/dooris-collector/'):
        runloop()
