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

config = ConfigParser.SafeConfigParser()
config.read('dooris.cfg')

shell = spur.SshShell(hostname=config.get('door', 'sshhost'),
                      username=config.get('door', 'sshuser'),
                      private_key_file=config.get('door', 'sshkey'))
doorstatus = shell.run(['cat', '/sys/class/gpio/gpio0/value'])

print 'door is closed' if doorstatus.output else 'door is open'

with open(config.get('general', 'classicoutputfile'), 'w') as f:
    f.write(doorstatus.output)
    f.write('{}\n'.format(datetime.datetime.now().strftime('%s')))
