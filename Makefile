# Makefile for source rpm: smartmontools
# $Id$
NAME := smartmontools
SPECFILE = $(firstword $(wildcard *.spec))

include ../common/Makefile.common
