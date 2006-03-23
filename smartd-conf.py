#!/usr/bin/python
# Copyright 2004 Red Hat, Inc. Distributed under the GPL.
# Author: Will Woods <wwoods@redhat.com>
import kudzu
import os
drives=kudzu.probe(kudzu.CLASS_HD,kudzu.BUS_IDE|kudzu.BUS_SCSI,kudzu.PROBE_ALL)

print """# /etc/smartd.conf

# Sample configuration file for smartd.  See man 5 smartd.conf.
# Home page is: http://smartmontools.sourceforge.net

# The file gives a list of devices to monitor using smartd, with one
# device per line. Text after a hash (#) is ignored, and you may use
# spaces and tabs for white space. You may use '\\' to continue lines.

# You can usually identify which hard disks are on your system by
# looking in /proc/ide and in /proc/scsi.

# The word DEVICESCAN will cause any remaining lines in this
# configuration file to be ignored: it tells smartd to scan for all
# ATA and SCSI devices.  DEVICESCAN may be followed by any of the
# Directives listed below, which will be applied to all devices that
# are found.  Most users should comment out DEVICESCAN and explicitly
# list the devices that they wish to monitor.
# DEVICESCAN

# First (primary) ATA/IDE hard disk.  Monitor all attributes
# /dev/hda -a

# Monitor SMART status, ATA Error Log, Self-test log, and track
# changes in all attributes except for attribute 194
# /dev/hdb -H -l error -l selftest -t -I 194

# A very silent check.  Only report SMART health status if it fails
# But send an email in this case"""

def getfile(fname):
    try:
	fh = open(fname)
        line = fh.read().rstrip()
	fh.close()
    except IOError:
	line = ''
    return line

for drive in drives:
    if getfile("/sys/block/%s/removable" % drive.device) == '0':
	driver = ''
	comment = ''
	if getfile("/sys/block/%s/device/vendor" % drive.device) == 'ATA':
	    driver = '-d ata '
	    if float(getfile("/sys/module/libata/version")) < 1.20:
		comment = "# not yet supported in this kernel version\n# "
	if not comment:
	    status = os.system("/usr/sbin/smartctl -i %s/dev/%s 2>&1 >/dev/null" %
		(driver, drive.device))
	    if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
		comment = "# smartctl -i returns error for this drive\n# "
	print "%s/dev/%s %s-H -m root" % (comment, drive.device, driver)

print """
# First two SCSI disks.  This will monitor everything that smartd can
# monitor.
# /dev/sda -d scsi
# /dev/sdb -d scsi

# HERE IS A LIST OF DIRECTIVES FOR THIS CONFIGURATION FILE
#   -d TYPE Set the device type to one of: ata, scsi
#   -T TYPE set the tolerance to one of: normal, permissive
#   -o VAL  Enable/disable automatic offline tests (on/off)
#   -S VAL  Enable/disable attribute autosave (on/off)
#   -H      Monitor SMART Health Status, report if failed
#   -l TYPE Monitor SMART log.  Type is one of: error, selftest
#   -f      Monitor for failure of any 'Usage' Attributes
#   -m ADD  Send warning email to ADD for -H, -l error, -l selftest, and -f
#   -M TYPE Modify email warning behavior (see man page)
#   -p      Report changes in 'Prefailure' Normalized Attributes
#   -u      Report changes in 'Usage' Normalized Attributes
#   -t      Equivalent to -p and -u Directives
#   -r ID   Also report Raw values of Attribute ID with -p, -u or -t
#   -R ID   Track changes in Attribute ID Raw value with -p, -u or -t
#   -i ID   Ignore Attribute ID for -f Directive
#   -I ID   Ignore Attribute ID for -p, -u or -t Directive
#   -v N,ST Modifies labeling of Attribute N (see man page)
#   -a      Default: equivalent to -H -f -t -l error -l selftest
#   -F TYPE Use firmware bug workaround. Type is one of: none, samsung
#   -P TYPE Drive-specific presets: use, ignore, show, showall
#    #      Comment: text after a hash sign is ignored
#    \      Line continuation character
# Attribute ID is a decimal integer 1 <= ID <= 255
# All but -d, -m and -M Directives are only implemented for ATA devices
#
# If the test string DEVICESCAN is the first uncommented text
# then smartd will scan for devices /dev/hd[a-l] and /dev/sd[a-z]
# DEVICESCAN may be followed by any desired Directives."""

