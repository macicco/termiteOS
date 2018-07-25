#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
'''
Raspberry PWM motor driver.


INTERFACE:

        * inherits several methods from rpiDRV8825Hut base class
                - betaMotor
                - pinout
                - microsteps
                - clutch()
                - reset()
                - sleep()
                - set_microsteps(microsteps)
                - sync(position)

        * Own methods:
                - setSpeed (radians/seconds)
                - setRPM(RPM)
                - SetPoint(setpoint)
                - goto() -> absolute SetPoint
                - move() -> relative SetPoint
                - stop()
                - isStopped
                - gotoEnd
                - pos

'''
from __future__ import print_function
import math
import time, datetime
import pigpio
import logging
import threading
import termiteOS.maths.hPID as PID
import termiteOS.drivers.rpi.rpiDRV8825Hat as rpihat

def threaded(fn):
    '''
    Multithread wrapper. Used as a function decorator
    '''
    def wrapper(*args, **kwargs):
        t1 = threading.Thread(target=fn, args=args, kwargs=kwargs)
        t1.start()
        return t1

    return wrapper

#Stepper raspberry implementation
class rpiSpeedPWM(rpihat.rpiDRV8825Hat):
    '''
    This class do the PWM control calling the underlying
    pigpiod daemon. 

    .. note:: Up to dates only PID control is implemented.
    '''
    def __init__(self, driverID,microsteps,FullTurnSteps,gear=1,name='Axis', raspberry='localhost'):
        super(rpiSpeedPWM, self).__init__(raspberry,driverID,microstepping=microsteps)
        self.logger = logging.getLogger(type(self).__name__)
        self.vmax=750
        self.name=name
        self.gear=gear
        self.STEP_PIN = self.pinout['STEP']
        self.DIR_PIN = self.pinout['DIR']
        self.pulseDuty = 0.5
        self.maxAccel=300
        self.FullTurnSteps=FullTurnSteps*self.microsteps
        self.minMotorStep = math.pi * 2 / float(self.FullTurnSteps)
        self._SetPoint=0
        self.freq = 0
        self.Vold=0
        self._trackSpeed=0
        self.stopPWM()
        self.RUN=True
        self.timesleep=0.1
        self.logger.debug("rpiSpeedPWM Controller created")

    def sync(self,newposition):
        '''Establish newposition as current possition (motorBeta)'''
        self.motorBeta=newposition

    def stop(self):
        '''Not implemented'''
        #TBD
        pass

    def stopPWM(self):
        '''Stop PWM generation without any check'''
        self.pi.hardware_PWM(self.STEP_PIN, 0, 0)
        self.logger.debug("STOPPED")

    @property
    def isStopped(self):
        '''True if is stopped, False otherwise'''
        try:
                PWMstop =  (self.pi.get_PWM_dutycycle(self.STEP_PIN) == 0) 
        except:
                PWMstop = True
        return PWMstop

    @property
    def gotoEnd(self):
        '''True if the axis finally arrive to destination(_SetPoint), False otherwise'''
        try:
                PWMstop =  (self.pi.get_PWM_dutycycle(self.STEP_PIN) == 0) 
        except:
                PWMstop = True
        stopped=PWMstop and  (self.motorBeta == self._SetPoint)
        return stopped

    def setRPM(self,rpm):
        '''Set and start PWM to obtain rpm'''
        v=rpm*2.*math.pi/60.
        self.setSpeed(v)
        self.logger.debug("RPM %f",v)

    def setSpeed(self, v):
        '''Set and start PWM to obtain radians/seconds'''
        #print("setSpeed V:", v)
        # v in radians/s    
        freq = 0
        #calculate direction of motion
        if self.dir * v < 0:
            self.dir = math.copysign(1, v)
            self.set_dir(self.dir)
        freq = round(abs(v) / self.minMotorStep)
        if freq >= self.maxPPS:
            freq = self.maxPPS
        self.freq=freq
        if self.freq!=0:
                self.pi.hardware_PWM(self.STEP_PIN, self.freq,self.pulseDuty * 1000000)
        else:
                self.pi.hardware_PWM(self.STEP_PIN, 0,0)
        self.logger.debug("PWM FREQUENCY:%f",self.freq)
        return self.freq

    def trackSpeed(self,trackSpeed):
        '''Set axis track speed. Track speed*timestep is add to the _SetPoint value '''
        self._trackSpeed=trackSpeed*self.gear*self.FullTurnSteps

    def rampUp(self,v,deltaT,out_min=-750,out_max=750):
        '''Limit motor speed changes to avoid axis stalling'''
        deltaV=(v-self.Vold)
        self.logger.debug("RAMPUPV DELTA_V:%f V:%f oldV:%f",deltaV,v,self.Vold)
        if abs(deltaV)>=self.maxAccel*deltaT:
            v=self.Vold+math.copysign(self.maxAccel*deltaT, deltaV)
            self.logger.debug("MAX ACCEL %f deltaT:%f",self.maxAccel*deltaT,deltaT)
        if v <= out_min:
                v=out_min
                self.logger.debug("MIN V")
        if v >= out_max:
                v=out_max
                self.logger.debug("MAX V")
        self.logger.debug("RAMPUP V:%f",v)
        self.Vold=v
        return v

    def move(self,relsetpoint):
        '''Relative movement'''
        self.logger.debug("RELATIVE MOVE TO:%f",relsetpoint)
        return self.goto(self._SetPoint+relsetpoint*self.gear*self.FullTurnSteps)

    def goto(self,setpoint,blocking=False):
        '''Absolute movement'''
        self._SetPoint=setpoint*self.gear*self.FullTurnSteps
        self.logger.debug("ABSOLUTED MOVE TO:%f",setpoint)
        if blocking:
                self.logger.debug("GOTO wait until finished")
                while not self.gotoEnd:
                        time.sleep(0.1)
                return True
        else:
                return False

    def SetPoint(self,setpoint):
        '''Establish the _SetPoint value'''
        self._SetPoint=setpoint*self.gear*self.FullTurnSteps

    @property
    def pos(self):
        '''Actual position (Corrected motorBeta)'''
        return self.motorBeta/(self.gear*self.FullTurnSteps)
        
    @threaded
    def run(self):
        '''
        The main loop. Do not exit until self.RUN is False
        '''
        self.T = time.time()

        _kp=0.015*16/self.microsteps
        _ki=0.001*16/self.microsteps
        _kd=0.00*16/self.microsteps

        pid=PID.PID(sampletime=self.timesleep,kp=_kp,ki=_ki,kd=_kd,out_min=-self.vmax,out_max=self.vmax)
        while self.RUN:
            #calculate the actual timestep
            now = time.time()
            deltaT = now - self.T
            self._SetPoint=self._SetPoint + deltaT*self._trackSpeed
            pid.SetPoint=self._SetPoint
            feedback=self.motorBeta
            v = pid.update(feedback)
            v=self.rampUp(v,deltaT,out_min=-self.vmax,out_max=self.vmax)
            self.setRPM(v)
            time.sleep(self.timesleep)
            print("%f %f %f %f %f" % (self._trackSpeed,pid.SetPoint,feedback,feedback-pid.SetPoint,v))
            self.logger.debug("PID error:%f v:%f",feedback-pid.SetPoint,v)
            self.T=now
        self.logger.critical("RUN END")




if __name__ == '__main__':
        logging.basicConfig(format='%(asctime)s PWMspeed:%(levelname)s %(message)s',level=logging.DEBUG)
        axis=rpiSpeedPWM(0,16,200,name='DummyAxis',raspberry='192.168.1.11',gear=1)
        runThread=axis.run()
        axis.goto(10,blocking=True)
        axis.RUN=False
        runThread.join()
        print(axis.isStopped)
        print(axis.motorBeta)

