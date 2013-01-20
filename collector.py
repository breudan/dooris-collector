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


class Collector:
    """Collects various Dooris sensor data and write output files"""

    def __init__(self):
        self.apiversion = 2
        self.config = ConfigParser.SafeConfigParser()
        self.config.read('dooris.cfg')
        with open('schema.json', 'r') as schf:
            self.schema = json.load(schf)
        try:
            with open(self.config.get('general', 'jsonoutputfile'),
                      'r') as oldjsonfile:
                oldjson = json.load(oldjsonfile)
            jsonschema.validate(oldjson, self.schema)
            if oldjson['apiversion'] == self.apiversion:
                self.output = oldjson
            else:
                self.output = {'apiversion': self.apiversion}
        except jsonschema.ValidationError, jsonschema.SchemaError:
            self.output = {'apiversion': self.apiversion}
        except IOError:
            self.output = {'apiversion': self.apiversion}

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
        now = int(datetime.datetime.now().strftime('%s'))
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
        now = int(datetime.datetime.now().strftime('%s'))
        if not 'router' in self.output:
            self.output['router'] = {'dhcp': '-1'}
        if self.output['router']['dhcp'] != dhcpclients:
            self.output['router']['dhcp'] = dhcpclients
            self.output['router']['last_change'] = now
        self.output['router']['last_update'] = now

    def write_output(self):
        """Collect data and write output files."""
        try:
            jsonschema.validate(self.output, self.schema)
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


if __name__ == "__main__":
    SCHED = Scheduler()
    COLL = Collector()
    SCHED.start()
    SCHED.add_interval_job(COLL.collect_and_write, minutes=2)
    while True:
        time.sleep(500)
