#!/usr/bin/python
# Copyright 2004 Red Hat, Inc. Distributed under the GPL.
# Author: Will Woods <wwoods@redhat.com>
import kudzu
drives=kudzu.probe(kudzu.CLASS_HD,kudzu.BUS_IDE|kudzu.BUS_SCSI,kudzu.PROBE_ALL)
for drive in drives:
    fh=open("/sys/block/%s/removable" % drive.device)
    if fh.read(1) == '0':
        print "/dev/%s -H -m root@localhost.localdomain" % drive.device
