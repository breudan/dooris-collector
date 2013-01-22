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

    def _ssh_exec(self, module, command):
        """Read config for module, execute command via SSH."""
        shell = spur.SshShell(hostname=self.config.get(module, 'sshhost'),
                              username=self.config.get(module, 'sshuser'),
                              port=int(self.config.get(module, 'sshport')),
                              private_key_file=self.config.get(module,
                                                               'sshkey'))
        try:
            result = shell.run(command).output
        except:
            # no difference in misconfiguration and actual errors.
            # might need improvement. :)
            result = '-1'
        return result

    def _update_result(self, module, value):
        """update output with new value for module"""
        now = int(datetime.datetime.now().strftime('%s'))
        if not module in self.output:
            self.output[module] = {value[0]: '-1'}
        if self.output[module][value[0]] != value[1]:
            self.output[module][value[0]] = value[1]
            self.output[module]['last_change'] = now
        self.output[module]['last_update'] = now

    def fetch_doorstatus(self):
        """Read door status via SSH to Raspi."""
        doorstatus = self._ssh_exec('door', ['cat',
                                             '/sys/class/gpio/gpio0/value'])
        doorstatus = doorstatus.strip()
        self._update_result('door', ('status', doorstatus))

    def fetch_routerstatus(self):
        """Read router status via SSH to router."""
        dhcpclients = self._ssh_exec('router', ['wc', '-l',
                                                '/tmp/dhcp.leases'])
        dhcpclients = dhcpclients.split()[0].strip()
        self._update_result('router', ('dhcp', dhcpclients))

    def fetch_terminal(self):
        """check if public terminal is on"""
        terminalstatus = self._ssh_exec('terminal', ['cat', 'status'])
        terminalstatus = terminalstatus.strip()
        self._update_result('terminal', ('status', terminalstatus))

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
        self.fetch_terminal()
        self.write_output()


if __name__ == "__main__":
    SCHED = Scheduler()
    COLL = Collector()
    SCHED.start()
    SCHED.add_interval_job(COLL.collect_and_write, minutes=2)
    while True:
        time.sleep(500)
