#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
'''
DIY DRV8825 driver  Hut interface.
This board has two DRV8825 able to driver 2 motors
See hardware termiteOS/driver/rpi/hardware

INTERFACE TO OTHER MODULES
- pinout
- microsteps
- clutch()
- reset()
- sleep()
- microsteping(microsteps)

'''

import pigpio



class rpiDRV8825Hut(object):
	def __init__(self,raspberry,driverID,**kwds):
		self.pi=pigpio.pi(raspberry)
                PINOUT={0:{'STEP':13,'DIR': 5,'ENABLE':21,'FAULT': 4,'RESET':12,'SLEEP': 6,'M0':20,'M1':19,'M2':16},\
                        1:{'STEP':18,'DIR':22,'ENABLE': 8,'FAULT':17,'RESET':25,'SLEEP':24,'M0':11,'M1': 9,'M2':10}}
                self.pinout=PINOUT[driverID]
		pi=self.pi
		pi.set_mode(self.pinout['STEP'], pigpio.OUTPUT)
		pi.set_mode(self.pinout['DIR'], pigpio.OUTPUT)
		pi.set_mode(self.pinout['ENABLE'], pigpio.OUTPUT)
		pi.set_mode(self.pinout['M2'], pigpio.OUTPUT)
		pi.set_mode(self.pinout['M1'], pigpio.OUTPUT)
		pi.set_mode(self.pinout['M0'], pigpio.OUTPUT)
		pi.set_mode(self.pinout['RESET'], pigpio.OUTPUT)
		pi.set_mode(self.pinout['SLEEP'], pigpio.OUTPUT)
		pi.set_mode(self.pinout['FAULT'], pigpio.INPUT)
		cb1 = self.pi.callback(self.pinout['STEP'], pigpio.RISING_EDGE, self.stepcounter)
		cb2 = self.pi.callback(self.pinout['FAULT'], pigpio.EITHER_EDGE, self.fault)
		self.clutch(False)


	def clutch(self,ON_OFF):
		self.pi.write(self.pinout['ENABLE'],ON_OFF)

	def microstepping(self,MICROSTEPS):
		'''
			M2 M1 M0
			0  0  0 Full step (2-phase excitation) with 71% current
			0  0  1 1/2 step (1-2 phase excitation)
			0  1  0 1/4 step (W1-2 phase excitation)
			0  1  1 8 microsteps/step
			1  0  0 16 microsteps/step
			1  0  1 32 microsteps/step
			1  1  0 32 microsteps/step
			1  1  1 32 microsteps/step

			RESET=HIGH DEVICE ENABLE
			SLEEP=HIGH DEVICE ENABLE
			ENABLE=LOW DEVICE ENABLE
		'''
		microstep_table={1:{'M2':False,'M1':False,'M0':False}, \
				 2:{'M2':False,'M1':False,'M0':True},  \
				 4:{'M2':False,'M1':True,'M0':False},  \
				 8:{'M2':False,'M1':True,'M0':True},   \
				 16:{'M2':True,'M1':False,'M0':False},  \
				 32:{'M2':True,'M1':False,'M0':True}}
		msteping=microstep_table[MICROSTEPS]
		self.microsteps=MICROSTEPS	
		self.pi.write(self.pinout['M2'], msteping['M2'])
		self.pi.write(self.pinout['M1'], msteping['M1'])
		self.pi.write(self.pinout['M0'], msteping['M0'])
		self.microstepping(MICROSTEPS)


        def reset(self):
                #reset
		pi.write(self.pinout['RESET'], False)
		time.sleep(0.5)
		pi.write(self.pinout['RESET'], True)
                #wake up
		pi.write(self.pinout['SLEEP'], True)

	def sleep(self,ON_OFF):
                NOT_ON_OFF=not ON_OFF
		pi.write(self.pinout['SLEEP'], NOT_ON_OFF)

	def stepcounter(self,gpio, level, tick):
		self.motorBeta=self.motorBeta+self.dir

	def fault(self,gpio, level, tick):
		if level==1:
			self.fault=True
		else:
			self.fault=False

if __name__ == '__main__':
    raspberry='192.168.1.11'
    m0 = rpiDRV8825Hut(raspberry,0)
    m0.clutch(True)
    m1 = rpiDRV8825Hut(raspberry,1)
    m1.clutch(True)

