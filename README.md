# Gcloud-Scheduled-Snapshots - A simple Google Cloud Compute Engine daily and weekly rotative scheduled snapshots

Version 0.0.5 Alpha

## Introduction

One of the nice features of the Infrastructure as a service platforms is how a DevOp can take a snapshot of an existing
disk and create a new server from it. In some cases the cost can be a few cents, a very reasonable price for this
feature.

Any DevOp can be tempted to use this snapshot feature as a cheap alternative to more traditional backup systems and
procedure and schedule the snapshots of their disks in the cloud on a time basis. Sadly, the Compute Engine of Google
Cloud Platform currently does not support any time scheduling feature.

Since this is a nice to have feature of the Google Compute Engine, there are several scripts out there that can help
DevOps with this task, but I wanted to do something easy to use and most of all: fully unattended.

So if you want to have a scheduled snapshots in your Google Compute Engine projects with some interesting features like
daily and weekly schedules, snapshots retention policies and programmable hour and minute of execution, please keep on
reading!

## What you need

This tool needs the following environment:

* A Python 2.7 runtime.
* A *NIX operating system. It has been tested in Ubuntu 16.04 and Mac OSX, but it should work on any modern *NIX.
* CRON and CRONTAB installed and enabled in your operating system.
* AT installed and enabled (Mac OSX users, please read this).
* A server to server JSON credentials file downloaded from *API Manager / Credentials*.

## How to install

### Ubuntu 16.04

#### Step 1. Update and upgrade your system

Make sure you are using the latest packages and versions.

```
sudo apt-get update
sudo apt-get upgrade
```

#### Step 1. Install Python tools

We will use *pip* install utility to get the latest version of the tool.

```
sudo apt-get install python-pip
```

#### Step 2. Install the gcloud-scheduled-snapshots tool

Use *pip* to download and install it. Root privileges not needed, a simple user works.

```
pip install gcloud-scheduled-snapshots
```

#### Step 3. Download the JSON credentials file

We need a JSON credentials file with permissions to manage snapshots and disks. Please read https://developers.google.com/identity/protocols/application-default-credentials

You can download your credentials from https://console.developers.google.com/project/_/apis/credentials

Now, save the file under /home/YOUR_USER/.local/YOUR_JSON_CREDENTIALS_FILE.json

#### Step 4. Edit the gss.ini configuration file

This configuration file has to be modified to enter the following information:

- Rename *gss-sample.ini* file to *gss.ini* the first time you install. If you are upgrading, check if there are new parameters needed, but defaults should work.
- Under *autentication/credentials* enter the full path to the JSON credentials file previously downloaded.
- In *project/id* enter the ID of the project. The ID is the string that must be in lowercase, don't use the project
NAME.
- There is also parameters to reconfigure the traces and logs. By default, the logs are stored in /home/YOUR_USER/.local/logs

#### Step 5. Add a new entry in the CRONTAB

Every day at 00:00 the main process of the tool will schedule at what time the snapshots must be execute. So we need to
add the following line to your crontab.

First open your crontab in edition mode:

```
crontab -e
```

Now paste the following line:
```
    0   0   *   *   *   $HOME/.local/bin/gcloud_schedule_snapshots --config $HOME/.local/etc/gss.ini
```

Save the changes. The tool is installed and configured. Now it's time to program the snapshots needed.

## How to program your automated snapshots

### How it works

The tool runs every day at 00:00. It scans all the existing snapshots, parsing their names looking for a specific
pattern describing the frecuency, the retention period and the time to launch the snapshot. When there is a match, the
process creates a programmed task with the AT command.

### The snapshot naming convention

The tool tries to find the snapshot names following this convention:

```
ANY_SNAPSHOT_NAME-FRECUENCY-RETENTION_PERIOD-EXECUTION_TIME
```

* ANY_SNAPSHOT_NAME: Any lowercase text can be used here to help to identify the snapshot.
* FRECUENCY: There are two possible values: *schedule-daily* if the snapshot is executed daily or *schedule-weekly* if
it's executed weekly.
* RETENTION_PERIOD: The amount of days a snapshot will be kept. After RETENTION_PERIOD plus 1, the snapshot will be
deleted. This value must be from 1 to 99 and must always have two digits.
* EXECUTION_TIME: Hour and minute of snapshot execution and retention deletion (if any). The format is HHMM and must
have two digits each. Four digits combined.

Example 1:
```
mytest-schedule-daily-07-0600
```

Every day at 06:00 AM the disk in the original snapshot will be used to create a new snapshot. Also at 06:00 AM
the 8th snapshot will be deleted, if it exists.

Example 2:
```
mytest-schedule-weekly-04-0800
```

Every week the same that the original snapshot was created at 08:00 AM the disk in the original snapshot will be used to
 create a new snapshot. Also at 08:00 AM the 5th snapshot will be deleted, if it exists.

## Troubleshooting

The log files are stored in *$HOME/.local/logs*

## Revisions

### Version 0.5 Alpha
- Moved default log file to root.
- Rename gss.ini to gss-smaple.ini to avoid the file to be overwritten when upgrading

### Version 0.4 Alpha
- Fixed reStructuredText and Markdown compatibility.
- Added 'executables' section to configuration file
- Force full path in 'at' commands

### Version 0.3 Alpha
- First public release. Use with caution.

## Collaborate

You can consider this tool as a work in progress, so please feel free to suggest and send pull requests if you want to.

## Legal

The software is provided 'as is'. Use it at your own risk, and keep in mind that you are playing with your data. So test,
test, test and test!
