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
#  python do_snapshot.py CREDENTIALS_FILE PROJECT ZONE DISKNAME SNAPSHOTNAME DESCRIPTION
#

import sys
import logging
import logging.config
import json
import subprocess
import ConfigParser

from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

def main(argv=None):
    if argv is None:
        argv = sys.argv

    numargs = len(argv)
    credentials_file = str(argv[1])
    project = str(argv[2])
    zone = str(argv[3])
    disk_name = str(argv[4])
    snapshot_name = str(argv[5])
    description = str(argv[6])

    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scopes=['https://www.googleapis.com/auth/compute'])
    service = discovery.build('compute', 'v1', credentials=credentials)
    disks = service.disks()
    request = disks.createSnapshot(project=project, zone=zone, disk=disk_name, body={'name':snapshot_name,'description':description})
    response = request.execute()

    return 0

if __name__ == "__main__":
    sys.exit(main())
