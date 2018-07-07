#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas

import sys
import yaml
import termiteOS.scripts

def launchmachine(yamlfile):
	with open(yamlfile) as y:
		doc=y.read()
	try:
		ydoc=yaml.load(doc)
	except:
		print("Launch:malformed yaml \n"+doc)
	print ydoc

if __name__ == '__main__':
 	if len(sys.argv)!=2:
		print("usage:"+sys.argv[0]+" yaml_file")
		exit(1)
	yamlfile=sys.argv[1]
 	print("Reading from:"+yamlfile)
	launchmachine(yamlfile)
	

