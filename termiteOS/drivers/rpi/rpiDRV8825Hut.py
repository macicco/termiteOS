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
- motorBeta
- pinout
- microsteps
- clutch()
- reset()
- sleep()
- set_microsteps(microsteps)
- sync(motorBeta) 

RASPBERRY B+ PWM PINOUT:
			12  PWM channel 0  All models but A and B
			13  PWM channel 1  All models but A and B
			18  PWM channel 0  All models
			19  PWM channel 1  All models but A and B
			CHOSE DIFERENT CHANNELS FOR EACH MOTOR !!

'''

import pigpio
import logging


class rpiDRV8825Hut(object):
	def __init__(self,raspberry,driverID,**kwds):
                PINOUT={0:{'STEP':13,'DIR': 5,'ENABLE':21,'FAULT': 4,'RESET':12,'SLEEP': 6,'M0':20,'M1':19,'M2':16},\
                        1:{'STEP':18,'DIR':22,'ENABLE': 8,'FAULT':17,'RESET':25,'SLEEP':24,'M0':11,'M1': 9,'M2':10}}
                self.pinout=PINOUT[driverID]
		self.pi=pigpio.pi(raspberry)
                self.logger = logging.getLogger(type(self).__name__)
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
                self.maxPPS = 200000
                self.dir=1
                self.motorBeta = 0
                if 'microstepping' in kwds.keys():
                        self.set_microsteps(kwds['microstepping'])
                else:
                        self.set_microsteps(8)
                self.reset(False)
		self.sleep(False)
		self.clutch(False)


	def clutch(self,ON_OFF):
		self.pi.write(self.pinout['ENABLE'],ON_OFF)
                if ON_OFF:
                        self.logger.debug("CLUTCH ON")
                else:
                        self.logger.debug("CLUTCH OFF")

	def set_microsteps(self,microsteps):
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
                if microsteps not in microstep_table.keys():
                        print("Bad microsteps paramater",microsteps)
                        return
		msteping=microstep_table[microsteps]
		self.microsteps=microsteps	
		self.pi.write(self.pinout['M2'], msteping['M2'])
		self.pi.write(self.pinout['M1'], msteping['M1'])
		self.pi.write(self.pinout['M0'], msteping['M0'])
		self.microsteps=microsteps
                self.logger.debug("SET MICROSTEPS=%i",microsteps)


        def set_dir(self,dir):
		self.pi.write(self.pinout['DIR'],dir > 0)

        def reset(self,ON_OFF):
                NOT_ON_OFF=not ON_OFF
		self.pi.write(self.pinout['RESET'], NOT_ON_OFF)
                if ON_OFF:
                        self.logger.debug("RESET")

	def sleep(self,ON_OFF):
                NOT_ON_OFF=not ON_OFF
		self.pi.write(self.pinout['SLEEP'], NOT_ON_OFF)
                if ON_OFF:
                        self.logger.debug("SLEEPPING")
                else:
                        self.logger.debug("WAKE UP")

        def sync(self,position):
                self.motorBeta=position

	def stepcounter(self,gpio, level, tick):
		self.motorBeta=self.motorBeta+self.dir

	def fault(self,gpio, level, tick):
		if level==1:
			self.fault=True
                        self.logger.error("MOTOR FAULT!")
		else:
			self.fault=False

        def test(self):
                for i in range(1600):
                        self.pi.write(self.pinout['STEP'], True)           
                        self.pi.write(self.pinout['STEP'], False)          

if __name__ == '__main__':
    raspberry='192.168.1.11'
    m0 = rpiDRV8825Hut(raspberry,0,microstepping=8)
    m0.test()
    m0.clutch(True)

    m1 = rpiDRV8825Hut(raspberry,1)
    m1.test()
    m1.clutch(True)

