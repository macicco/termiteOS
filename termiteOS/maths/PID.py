#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
'''
copy from https://gist.github.com/chaosmail/8372717 
Thanks chaosmail!
'''
from __future__ import print_function
from __future__ import division

def PID(y, yc, h=1, Ti=1, Td=1, Kp=1, u0=0, e0=0):
	"""Calculate System Input using a PID Controller

	Arguments:
	y  .. Measured Output of the System
	yc .. Desired Output of the System
	h  .. Sampling Time
	Kp .. Controller Gain Constant
	Ti .. Controller Integration Constant
	Td .. Controller Derivation Constant
	u0 .. Initial state of the integrator
	e0 .. Initial error

	Make sure this function gets called every h seconds!
	"""
	
	# Step variable
	k = 0

	# Initialization
	ui_prev = u0
	e_prev = e0

	while 1:

		# Error between the desired and actual output
		e = yc - y

		# Integration Input
		ui = ui_prev + 1/Ti * h*e
		# Derivation Input
		ud = 1/Td * (e - e_prev)/h

		# Adjust previous values
		e_prev = e
		ui_prev = ui

		# Calculate input for the system
		u = Kp * (e + ui + ud)
		
		k += 1

		yield u


if __name__ == '__main__':
        y=0
        yc=0
        pid=PID(y, yc, h=1, Ti=1, Td=1, Kp=1, u0=0, e0=0)
        for i in range(1000):
                if (i % 100) == 0:
                      yc=1.
                if ((i+50) % 100) == 0:                
                       yc=0.
                y=pid.next()
                print("y=%f yc=%f i=%i" % (y,yc,i))



