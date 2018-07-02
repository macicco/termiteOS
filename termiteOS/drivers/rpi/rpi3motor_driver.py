#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

'''
Stepper classes. It use the 'wave' funtionality include in 
pigpio library to send pulses to a drv8825 driver. Tested with
the hardware showed in the "connections.png" file.

pigpio only has one DMA channel dedicate to wave. Thus we need
to compose all waves for all motos prior to send them throught
DMA channel. It is done in chuncks of pulses. As side effect is 
not posible to driver a single motor without command the others. 
For the same reason motor are perfectly syncronize each other.



interface:

* addStepper(stepperInstance) ->add a new motor to the engine.
* move(steps_list) 	-> move n steps relative to the current position
* rotate(degrees_list) 	-> go to an absolute position in degrees
* rmp(rpm0_list)       	-> set speed

In this context *_list are used to pass arguments because  we don't know 
how many steppers are in the engine at programing time.

* 
'''


import math
import time,datetime
import pigpio
import moduleSkull
import messages_pb2 as msg
from config import *


CHUNKSIZE=20000
PULSESIZE=5

raspberry='192.168.1.11'

class engine(moduleSkull.module):

	def __init__(self,name,port,hubport=False):
		super(engine,self).__init__(name,port,hubport)
		CMDs={ 
		"status": self.status, \
		"microsteps": self.microstepping, \
		"clutch": self.cmd_clutch, \
		"rpm": self.cmd_rpm, \
		"rotate": self.cmd_rotate \
		}
		self.addCMDs(CMDs)
		if hubport:
			self.register()
		self.pi=pigpio.pi(raspberry)
		self.pi.wave_clear()
		self.steppers=[]
		self.old_wid=9999
		self.WIDs=[]


	def cmd_clutch(self,arg):
		ON_OFF=bool(int(arg))
		self.clutch(ON_OFF)
		return 	ON_OFF

	def microstepping(self,MICROSTEPPING):
		m=int(MICROSTEPPING)
		for i,stepper,in enumerate(self.steppers):
			stepper.microstepping(m)

	def cmd_rpm(self,arg):
		arg=arg.split(' ')
		try:
			v0=float(arg[0])
			v1=float(arg[1])
		except:
			return "BAD SPEED:",arg
		return 	self.rpm((v0,v1))

	def cmd_rotate(self,arg):
		arg=arg.split(' ')
		try:
			r0=int(arg[0])
			r1=int(arg[1])
		except:
			return "BAD SETPOINT:",arg
		return self.rotate((r0,r1))


	def addStepper(self,stepper):
		self.steppers.append(stepper)
		print "Added new stepper #",len(self.steppers),stepper.name

	def clutch(self,ON_OFF):
		for i,stepper,in enumerate(self.steppers):
			stepper.clutch(ON_OFF)

	def rpm(self,rpm_list):
		if False:
			self.pi.wave_clear()

		for i,rpm,in enumerate(rpm_list):
			self.steppers[i].setRPM(rpm)

		return True

	def move(self,steps_list):
		for i,steps,in enumerate(steps_list):
			self.steppers[i].move(steps)
		return True
	
	def rotate(self,degrees_list):
		for i,degrees,in enumerate(degrees_list):
			self.steppers[i].rotate(degrees)
		print self.status()
		return True


	def _sendWave(self):
		'''
		This function does not return until previus wave is execute and deleted.
		This works as realtime sync since each wave has a fix CHUNKSIZE lasting.
		'''
		wid = self.pi.wave_create()
		self.WIDs.append(wid)
		#print wid
		self.pi.wave_send_using_mode(wid, pigpio.WAVE_MODE_ONE_SHOT_SYNC)
		while self.pi.wave_tx_at()==self.old_wid :
				pass
		if self.old_wid!=9999:
			self.pi.wave_delete(self.old_wid)
		self.old_wid=wid
		'''
		while self.pi.wave_tx_at()==self.old_wid :
				pass
		
		print self.old_wid,wid
		#chapu
		n=4
		if len(self.WIDs)>n:
			#print wid,self.pi.wave_tx_at(),"DELETING:",self.WIDs[:-1]
			for i in self.WIDs[:-1]:
				self.pi.wave_delete(i)
			self.WIDs=[wid]
		self.old_wid=wid
		'''

	def _areSyncronized(self):
		answer=True
		for i,stepper,in enumerate(self.steppers):
			answer=answer and stepper.syncronized
		return answer
		
	def checkWaveBuffer(self):
		maxCBS=self.pi.wave_get_max_cbs()
		maxPulse=self.pi.wave_get_max_pulses()
		maxMicros=self.pi.wave_get_max_micros()
	
		CBS=self.pi.wave_get_cbs()
		Pulse=self.pi.wave_get_pulses()
		Micros=self.pi.wave_get_micros()
		print "CBS Pulses, Micros (ACTUAL/MAX)",CBS,maxCBS,Pulse,maxPulse,Micros,maxMicros

	def run(self):
	  	while self.RUN:
			for i,stepper,in enumerate(self.steppers):
				stepper.waveChunk()
			self._sendWave()
			print self.pi.wave_get_cbs()

		print "MOTORS STOPPED"

	def status(self,arg=''):
		motorstatus=msg.MOTORS_STATUS()
		for i,stepper,in enumerate(self.steppers):
			status=motorstatus.MOTORS.add()
			status.CopyFrom(stepper.status())
		return motorstatus



class stepper(object):
	def __init__(self,name,stepsPerTurn,STEP_PIN,DIR_PIN,ENABLE_PIN,FAULT_PIN):
		self.pi=pigpio.pi(raspberry)
		self.setPINs(STEP_PIN,DIR_PIN,ENABLE_PIN,FAULT_PIN)
		cb1 = self.pi.callback(self.STEP_PIN, pigpio.RISING_EDGE, self.feedback)
		cb2 = self.pi.callback(self.FAULT_PIN, pigpio.EITHER_EDGE, self.fault)
		self.stepsPerTurn=stepsPerTurn
		self.microsteps=0
		self.name=name
		self.dir=1
		self.beta=0
		self.betaR=0
		self.betaTarget=0
		self.rpm=0
		self.rpmTarget=0
		self.freq=0
		self.steps_rest=0
		self.syncronized=False
		self.fault=False


	def setPINs(self,STEP_PIN,DIR_PIN,ENABLE_PIN,FAULT_PIN):
		self.STEP_PIN=STEP_PIN
		self.DIR_PIN=DIR_PIN
		self.ENABLE=ENABLE_PIN
		self.FAULT_PIN=FAULT_PIN

		pi=self.pi
		pi.set_mode(self.STEP_PIN, pigpio.OUTPUT)
		pi.set_mode(self.DIR_PIN, pigpio.OUTPUT)
		pi.set_mode(self.ENABLE, pigpio.OUTPUT)
		self.clutch(False)

		pi.set_mode(self.FAULT_PIN, pigpio.INPUT)

	def clutch(self,ON_OFF):
		self.pi.write(self.ENABLE,ON_OFF)

	def setRPM(self,rpm):
		self.rpmTarget=abs(rpm)
		self.rpm=self.rpmTarget
		self.freq=self.rpmTarget*self.microsteps*self.stepsPerTurn/60.

	def move(self,steps):
	   	self.syncronized=False
		self.betaTarget=self.beta+steps


	def rotate(self,degrees):
	   	self.syncronized=False
		target=degrees*(self.stepsPerTurn/360.)*self.microsteps
		self.betaTarget=target

	def feedback(self,gpio, level, tick):
		'''
		dir=self.pi.read(self.DIR_PIN)
		dir=1
		if dir==1:
			dir=1
		else:
			dir=-1
		self.betaR=self.betaR+1*dir
		'''
		self.betaR=self.betaR+self.dir
		#print self.betaR

	def fault(self,gpio, level, tick):
		if level==1:
			self.fault=True
		else:
			self.fault=False
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
		self.pi.write(self.M2_PIN, msteping['M2'])
		self.pi.write(self.M1_PIN, msteping['M1'])
		self.pi.write(self.M0_PIN, msteping['M0'])

	def auxPINs(self,RESET_PIN,SLEEP_PIN,M0_PIN,M1_PIN,M2_PIN,MICROSTEPS):
		pi=self.pi
		self.M0_PIN=M0_PIN
		self.M1_PIN=M1_PIN
		self.M2_PIN=M2_PIN
		pi.set_mode(M2_PIN, pigpio.OUTPUT)
		pi.set_mode(M1_PIN, pigpio.OUTPUT)
		pi.set_mode(M0_PIN, pigpio.OUTPUT)
		pi.set_mode(RESET_PIN, pigpio.OUTPUT)
		pi.set_mode(SLEEP_PIN, pigpio.OUTPUT)
		pi.write(RESET_PIN, False)
		time.sleep(0.5)
		print "Resetting driver.."
		pi.write(RESET_PIN, True)
		pi.write(SLEEP_PIN, True)
		self.microstepping(MICROSTEPS)


	def makeWave(self,steps):
		wave=[]
		if steps !=0:
			length=CHUNKSIZE/steps
		else:
			length=CHUNKSIZE
		for s in range(0,CHUNKSIZE,PULSESIZE):			
			if ((s) % length) == 0:
				wave.append(pigpio.pulse(1<<self.STEP_PIN,0,PULSESIZE))
			else:
				wave.append(pigpio.pulse(0, 1<<self.STEP_PIN,PULSESIZE))
		return wave

	def waveChunk(self):
		wave=[]
		lasting=CHUNKSIZE
		tmin=10
		delta=self.betaTarget-self.beta

		if delta*self.dir<0:
			self.steps_rest=-self.steps_rest
			self.dir=self.dir*-1
			dirwave=[]
			dirwave.append(pigpio.pulse(0,1<<self.DIR_PIN,tmin))
			if self.dir>0:
				dirwave.append(pigpio.pulse(1<<self.DIR_PIN,0,tmin))
			else:
				dirwave.append(pigpio.pulse(0,1<<self.DIR_PIN,tmin))
			pulses=self.pi.wave_add_generic(dirwave)

		dir=self.dir
		delta=abs(delta)
		self.rpm=self.rpmTarget
		if delta<1:
			self.syncronized=True
			self.rpm=0
		else:
			self.syncronized=False
			self.rpm=self.rpmTarget

		if delta<1 or self.freq==0:
			steps=0
			self.steps_rest=0
			wave=self.makeWave(0)
			#wave.append(pigpio.pulse(0, 1<<self.STEP_PIN, lasting))
			self.pi.wave_add_generic(wave)
			return 	self.beta
	

		steps_float=self.freq*lasting/1000000.
		steps=int(steps_float)
		self.steps_rest=self.steps_rest+(steps_float-steps)
		#print self.name,steps_float,steps,self.steps_rest,delta
		if steps==0 and abs(self.steps_rest)<1:
			wave=self.makeWave(0)
			#wave.append(pigpio.pulse(0, 1<<self.STEP_PIN, lasting))
			self.pi.wave_add_generic(wave)
			return 	self.beta


		if abs(self.steps_rest)>=1:
			#print "STEP REST",int(self.steps_rest),self.steps_rest
			steps=steps+int(self.steps_rest)
			self.steps_rest=self.steps_rest-int(self.steps_rest)

		if delta<steps:
			#Last pulses
			steps=int(round(delta))
			self.steps_rest=0

		t=0.5*lasting/steps   #time in micros

		wave=self.makeWave(steps)
		'''
		for i in range(steps):
			wave.append(pigpio.pulse(0, 1<<self.STEP_PIN, t))
			wave.append(pigpio.pulse(1<<self.STEP_PIN, 0, t))
		'''
		trest=lasting-steps*t
		#print trest,steps*t
		self.pi.wave_add_generic(wave)

		self.beta=self.beta+steps*dir
		return self.beta

		
	def status(self):
		motorstatus=msg.MOTOR_STATUS()
		motorstatus.name=self.name
		motorstatus.unixtime=time.time()
		motorstatus.dir=int(self.dir)
		motorstatus.steps.commanded=int(self.betaTarget)
		motorstatus.steps.actual=int(self.beta)
		motorstatus.steps.feedback=int(self.betaR)
		motorstatus.speed.commanded=int(self.rpmTarget)
		motorstatus.speed.actual=int(self.rpm)
		motorstatus.fault=self.fault
		motorstatus.sync=self.syncronized
		return motorstatus



if __name__ == '__main__':
	port=servers['zmqMotorDriverCmdPort']
	engineport=servers['zmqEngineCmdPort']
  	#e=engine('engine0',port,engineport)
	e=engine('engine0',port)
	#STEP_PIN,DIR_PIN,ENABLE_PIN,FAULT_PIN
	ra=stepper("RA",200,13,5,21,4)
	#RESET_PIN,SLEEP_PIN,M0_PIN,M1_PIN,M2_PIN,MICROSTEPS
	ra.auxPINs(12,6,20,19,16,16)
	dec=stepper("DEC",200,18,22,8,17)
	dec.auxPINs(25,24,11,9,10,16)
	e.addStepper(ra)
	e.addStepper(dec)
	v=200
	e.rpm((v,v))
	#e.rotate((360*30,360*30))
	e.run()
	exit()

	e.rpm((40,200))

	while True:
		v=30
		e.rpm((v,v))
		e.rotate((360*3,-360*3))
		time.sleep(0.5)
		e.rotate((0,0))
		time.sleep(0.5)

	while True:
		for v in range(10,340,10):
			e.rpm((v,v))
			e.rotate((180,180))
			e.rotate((0,0))
			time.sleep(1)
	
		for v in range(340,10,-10):
			e.rpm((v,v))
			e.rotate((180,180))
			e.rotate((0,0))
			time.sleep(1)

	d=1
		
	while True:
		q0=int(200*16*3/(360.))
		q1=int(48*16*3/(360.))
		e.move((d*q0,d*q1))
		#time.sleep(0.1)
		d=d*-1
	e.rpm((300,200))		
	e.move((200*16*50,48*16*5))
	print "======================="
	e.rpm((60*1,60*1))
	e.move((-200*16*5,-48*16*5))				
	print "======================="
	e.rpm((0.1,1))
	e.move((200*16,48*16))
'''
'''


