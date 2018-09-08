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


def threaded(fn):
    '''
    Multithread wrapper. Used as a function decorator
    '''
    def wrapper(*args, **kwargs):
        t1 = threading.Thread(target=fn, args=args, kwargs=kwargs)
        t1.start()
        return t1

    return wrapper

#general speed actuator virtual class
class rpiSpeed:
    '''
    This class do the speed control calling the underlying
    pigpiod daemon. 

    .. note:: Up to dates only PID and trapeze control is implemented.
    '''
    def __init__(self,gear=1,name='Axis'):
        self.logger = logging.getLogger(type(self).__name__)
        self.name=name
        self.gear=gear
        self._SetPoint=0
        self.freq = 0
        self._trackSpeed=0
        self.RUN=True
        self.logger.debug("rpiSpeed Controller created")

    def sync(self,newposition):
        '''Establish newposition as current possition (motorBeta)'''
        self.motorBeta=newposition

    def stop(self):
        '''Not implemented'''
        #TBD
        pass

    @property
    def gotoEnd(self):
        '''True if the axis finally arrive to destination(_SetPoint), False otherwise'''
        stopped= (self.motorBeta == self._SetPoint)
        return stopped

    def setRPS(self,rps):
        '''Turn at v=rps'''
        v=rps*2*math.pi
        self.setSpeed(v)
        self.logger.debug("RPS %f",v)

    def setRPM(self,rpm):
        '''Turn at v=rpm'''
        v=rpm*2*math.pi*60
        self.setSpeed(v)
        self.logger.debug("RPM %f",v)

    def setSpeed(self, v):
        '''Turn at v=radians/seconds virtual class. Do nothing'''
        return 

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

        _kp=100
        _ki=0.00
        _kd=0.00
        pid_control=PID.PID(timestep=self.timesleep,acceleration=self.acceleration, \
                        kp=_kp,ki=_ki,kd=_kd,out_min=-self.vmax,out_max=self.vmax)

        trapeze_control=trapeze.trapeze(timestep=self.timesleep,acceleration=self.acceleration, \
                                out_min=-self.vmax,out_max=self.vmax)

        if True:
                control=trapeze_control
        else:
                control=pid_control

        while self.RUN:
            #calculate the actual timestep
            now = time.time()
            deltaT = now - self.T
            self._SetPoint=self._SetPoint + deltaT*self._trackSpeed
            feedback=self.motorBeta
            v = control.update(self._SetPoint,feedback)
            self.setRPS(v/(self.FullTurnSteps*self.gear))
            time.sleep(self.timesleep)
            print("%f %f %f %f %f" % (self._trackSpeed,self._SetPoint,feedback,feedback-self._SetPoint,v))
            self.logger.debug("PID error:%f v:%f",feedback-self._SetPoint,v)
            self.T=now
        self.logger.critical("RUN END")




if __name__ == '__main__':
        logging.basicConfig(format='%(asctime)s PWMspeed:%(levelname)s %(message)s',level=logging.DEBUG)
        axis=rpiSpeed(name='DummyAxis',gear=100)
        runThread=axis.run()
        axis.goto(.5,blocking=True)
        axis.RUN=False
        runThread.join()
        print(axis.isStopped)
        print(axis.motorBeta)

