# coding=utf-8

"""
   Copyright 2017 Diego Parrilla Santamaría

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

#
#  python schedule_snapshots.py --config CONFIG_FILE.INI
#

import sys
import getopt
import logging
import logging.config
import json
import subprocess
import ConfigParser
import os

from datetime import datetime, timedelta
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

DEFAULT_CONFIG_FILE = 'etc/gss.ini'

GCE_SCOPES = ['https://www.googleapis.com/auth/compute']
GCE_SERVICE_VERSION = 'v1'
GCE_SERVICE_TYPE = 'compute'

CONFIG_PROJECT_KEY_ID = 'id'
CONFIG_PROJECT_SECTION = 'project'
CONFIG_AUTHENTICATION_KEY_CREDENTIALS = 'credentials'
CONFIG_AUTHENTICATION_SECTION = 'authentication'
CONFIG_EXECUTABLE_SECTION = 'executables'
CONFIG_EXECUTABLE_DELETE_SNAPSHOT = 'delete_snapshot'
CONFIG_EXECUTABLE_DO_SNAPSHOT = 'do_snapshot'
CONFIG_EXECUTABLE_PATH = 'path'

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def dt_parse(t):
    ret = datetime.strptime(t[0:16], '%Y-%m-%dT%H:%M')
    if t[18] == '+':
        ret += timedelta(hours=int(t[19:22]), minutes=int(t[23:]))
    elif t[18] == '-':
        ret -= timedelta(hours=int(t[19:22]), minutes=int(t[23:]))
    return ret


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            initfile = DEFAULT_CONFIG_FILE
            options, remainder = getopt.getopt(argv[1:], 'h:c', ['help', 'config='])
            for opt, arg in options:
                if opt in ('-c', '--config'):
                    initfile = arg
                elif opt in ('-h', '--help'):
                    print "python schedule_snapshots.py --config CONFIG_FILE.INI"
                    return 0
        except getopt.error, msg:
            raise Usage(msg)

        logging.config.fileConfig(initfile)
        logging.captureWarnings(True)

        logger_ = logging.getLogger(__name__)

        config = ConfigParser.ConfigParser()
        config.read(initfile)

        credentials_file = config.get(CONFIG_AUTHENTICATION_SECTION, CONFIG_AUTHENTICATION_KEY_CREDENTIALS)
        project = config.get(CONFIG_PROJECT_SECTION, CONFIG_PROJECT_KEY_ID)
        executable_delete_snapshot = config.get(CONFIG_EXECUTABLE_SECTION, CONFIG_EXECUTABLE_DELETE_SNAPSHOT)
        executable_do_snapshot = config.get(CONFIG_EXECUTABLE_SECTION, CONFIG_EXECUTABLE_DO_SNAPSHOT)
        path = config.get(CONFIG_EXECUTABLE_SECTION, CONFIG_EXECUTABLE_PATH)

        logger_.debug("CREDENTIALS FILE:%s" % credentials_file)
        logger_.debug("PROJECT:%s" % project)
        logger_.debug("EXECUTABLES PATH:%s" % path)
        logger_.debug("EXECUTABLE DO SNAPSHOT:%s" % executable_do_snapshot)
        logger_.debug("EXECUTABLE DELETE SNAPSHOT:%s" % executable_delete_snapshot)

        scopes = GCE_SCOPES
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scopes=scopes)
        service = discovery.build(GCE_SERVICE_TYPE, GCE_SERVICE_VERSION, credentials=credentials)

        if project is not None:
            # Iterate over all available snapshots in the project and save them for later use
            current_snapshots = []
            snapshots = service.snapshots()
            request = snapshots.list(project=project)
            while request is not None:
                response = request.execute()
                if 'items' in response:
                    for snapshot in response['items']:
                        current_snapshots.append(snapshot)
                request = snapshots.list_next(previous_request=request, previous_response=response)

            # Check for all available snapshot files. Parse them to find the convention
            for snapshot in current_snapshots:
                id = snapshot['id']
                name = snapshot['name']
                source_disk_id = snapshot['sourceDiskId']
                source_disk = snapshot['sourceDisk']
                created_at = dt_parse(snapshot['creationTimestamp'])
                zone = None
                source_disk_name = None
                backup_type = None
                retention = None
                try:
                    zone = source_disk.split('/zones/')[1].split('/')[0]
                except:
                    pass

                try:
                    source_disk_name = source_disk.split('/disks/')[1]
                except:
                    pass

                if 'schedule-daily' in name:
                    backup_type = 'daily'

                if 'schedule-weekly' in name:
                    backup_type = 'weekly'

                if backup_type is not None:
                    snapshot_minutes = None
                    snapshot_hour = None
                    retention = None
                    try:
                        snapshot_minutes = ('00%i' % int(name[-2:]))[-2:]
                        snapshot_hour = ('00%i' % int(name[-4:-2]))[-2:]
                    except:
                        pass

                    try:
                        retention = int(name[-7:-5])
                    except:
                        pass

                    logger_.debug('%s %s %s %s %s %s %s %s' % (
                    name, zone, backup_type, created_at, snapshot_hour, snapshot_minutes, retention, source_disk_name))

                if backup_type is not None and snapshot_hour is not None and snapshot_minutes is not None and retention is not None and zone is not None:
                    if backup_type == 'weekly':
                        # if weekly backup, then rotation and retetion is weekly too
                        retention *= 7
                    if backup_type == 'daily' or created_at.weekday() == datetime.today().weekday():
                        # If daily backup or is the day of the weekly backup, go for it
                        logger_.info("Schedule snapshot for today: %s, %s, %s, %s, %s, %s" % (
                            id, name, backup_type, retention, snapshot_hour, snapshot_minutes))
                        description = "Scheduled snapshot launched on %s at %s:%s" % (
                            datetime.strftime(datetime.today(), "%Y-%m-%d"), snapshot_hour, snapshot_minutes)

                        snapshot_name = '%s%s-%s' % (name.split('schedule-%s' % backup_type)[0], backup_type,
                                                     datetime.strftime(datetime.today(), "%Y-%m-%d"))
                        # The command to schedule today
                        create_command = """%s/%s %s %s %s %s %s \"%s\" """ % (
                        path, executable_do_snapshot, credentials_file, project, zone, source_disk_name, snapshot_name, description)

                        at_command = """`echo '%s' | at %s%s`""" % (create_command, snapshot_hour, snapshot_minutes)
                        subprocess.call(at_command, shell=True)

                        # Now we have to schedule the command to delete the rotational snapshot
                        # We are going to figure out the snapshot based on the name and create a delete command
                        # Does exists a snapshot made X days ago with the same string in the name?
                        old_snapshot_name = '%s%s-%s' % (name.split('schedule-%s' % backup_type)[0], backup_type,
                                                         datetime.strftime(datetime.today() - timedelta(days=retention),
                                                                           "%Y-%m-%d"))
                        for snapshot in current_snapshots:
                            if snapshot['name'] == old_snapshot_name:
                                # Ok, we found a snapshot. Let's create the command to delete it.
                                logger_.info("Schedule delete for today: %s" % old_snapshot_name)
                                # The command to schedule DELETE today
                                # The command to schedule today
                                delete_command = """%s/%s %s %s %s """ % (
                                path, executable_delete_snapshot, credentials_file, project, old_snapshot_name)
                                at_command = """`echo '%s' | at %s%s`""" % (
                                delete_command, snapshot_hour, snapshot_minutes)
                                subprocess.call(at_command, shell=True)
        return 0
    except Usage, err:
        print >> sys.stderr, err.msg
        print >> sys.stderr, "For help use --help"
        return 2


if __name__ == "__main__":
    sys.exit(main())



