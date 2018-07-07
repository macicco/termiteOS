#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas

import termiteOS.moduleSkull as moduleSkull
import time

def test_one():
	name='test_one'
	moduletype='hub'
	port=5000
	parent_host='localhost'
	parent_port=''
	e=moduleSkull.test_class(name,moduletype,port,parent_host,parent_port)
	e.end()


