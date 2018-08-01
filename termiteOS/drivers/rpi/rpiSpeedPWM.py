#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
'''
Raspberry PWM motor driver.
'''
from __future__ import print_function
import math
import time, datetime
import pigpio
import logging
import threading
import termiteOS.maths.hPID as PID
import termiteOS.maths.trapeze as trapeze
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
        self.vmax=750*FullTurnSteps*microsteps*gear/60
        self.acceleration=300*FullTurnSteps*microsteps*gear/60
        self.name=name
        self.gear=gear
        self.STEP_PIN = self.pinout['STEP']
        self.DIR_PIN = self.pinout['DIR']
        self.pulseDuty = 0.5
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

    def setRPS(self,rps):
        '''Set and start PWM to turn at v=rps'''
        v=rps*2*math.pi
        self.setSpeed(v)
        self.logger.debug("RPS %f",v)

    def setRPM(self,rpm):
        '''Set and start PWM to turn at v=rpm'''
        v=rpm*2*math.pi*60
        self.setSpeed(v)
        self.logger.debug("RPM %f",v)

    def setSpeed(self, v):
        '''Set and start PWM to to turn at v=radians/seconds'''
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

    def move(self,relsetpoint):
        '''Relative movement'''
        self.logger.debug("RELATIVE MOVE TO:%f",relsetpoint)
        return self.goto(self._SetPoint+relsetpoint*self.gear*self.FullTurnSteps)

    def goto(self,setpoint,blocking=False):
        '''Absolute movement'''
        self.SetPoint(setpoint)
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
        #IMPORTANT! calculation are done in realsteps (Setpoint, _trackSpeed, v..)
        self.T = time.time()

        _kp=50
        _ki=0.00
        _kd=0.00

        pid=PID.PID(timestep=self.timesleep,acceleration=self.acceleration, \
                        kp=_kp,ki=_ki,kd=_kd,out_min=-self.vmax,out_max=self.vmax)
        #pid=trapeze.trapeze(timestep=self.timesleep,acceleration=self.acceleration, \
        #                        out_min=-self.vmax,out_max=self.vmax)
        while self.RUN:
            #calculate the actual timestep
            now = time.time()
            deltaT = now - self.T
            self._SetPoint=self._SetPoint + deltaT*self._trackSpeed
            feedback=self.motorBeta
            v = pid.update(self._SetPoint,feedback)
            self.setRPS(v/(self.FullTurnSteps*self.gear))
            time.sleep(self.timesleep)
            print("%f %f %f %f %f" % (self._trackSpeed,self._SetPoint,feedback,feedback-self._SetPoint,v))
            self.logger.debug("PID error:%f v:%f",feedback-self._SetPoint,v)
            self.T=now
        self.logger.critical("RUN END")




if __name__ == '__main__':
        logging.basicConfig(format='%(asctime)s PWMspeed:%(levelname)s %(message)s',level=logging.DEBUG)
        axis=rpiSpeedPWM(0,16,200,name='DummyAxis',raspberry='192.168.1.11',gear=100)
        runThread=axis.run()
        axis.goto(1,blocking=True)
        axis.RUN=False
        runThread.join()
        print(axis.isStopped)
        print(axis.motorBeta)

