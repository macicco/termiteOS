#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
'''
Conection HUB
'''
from __future__ import print_function
import termiteOS.moduleSkull as moduleSkull


class hub(moduleSkull.module):
	def __init__(self,name,port,parent_host,parent_port):
		super(hub,self).__init__(name,'hub',port,parent_host,parent_port)

def runhub(name,port,parent_host='',parent_port=False):
	s=hub(name,port,parent_host,parent_port)
	try:
		s.run()
	except:
		s.end()

if __name__ == '__main__':
  	runhub('ROOTHUB',5000)




