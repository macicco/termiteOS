#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
from __future__ import print_function
import logging
import time
from termiteOS.drivers.rpi import rpiSpeedPWM as AxisDriver


class motorHub:
    def __init__(self,FullTurnSteps=200,microstepping=32,raspberry='localhost'):
        self.logger = logging.getLogger(type(self).__name__)
        self.axis1 = AxisDriver.rpiSpeedPWM(0,microstepping,FullTurnSteps,name='RA',raspberry=raspberry,gear=100)
        self.axis2 = AxisDriver.rpiSpeedPWM(1,microstepping,FullTurnSteps,name='DEC',raspberry=raspberry,gear=100)
        self.run()

    def run(self):
        self.threadAxis1=self.axis1.run()
        self.threadAxis2=self.axis2.run()

    def goto(self, x, y, blocking=False):
        self.axis1.goto(x, blocking=False)
        self.axis2.goto(y, blocking=False)
        if blocking:
                #dont work
                self.logger.debug("SLEW: wait until finished")
                while not self.isStopped:
                        time.sleep(0.1)
                return True
        else:
                return False

    def sync(self, x, y):
        self.axis1.sync(x)
        self.axis2.sync(y)

    @property
    def gotoEnd(self):
        return (self.axis1.gotoEnd and self.axis2.gotoEnd)
    
    @property
    def isStopped(self):
        return (self.axis1.isStopped and self.axis2.isStopped)

    def stop(self):
        self.logger.debug("STOP CURRENT MOVEMENTS")
        self.axis1.stop()
        self.axis2.stop()

    def setRPM(self, vx, vy):
        self.axis1.setRPM(vx)
        self.axis2.setRPM(vy)

    def setSpeed(self, vx, vy):
        self.axis1.setSpeed(vx)
        self.axis2.setSpeed(vy)

    def setTrackSpeed(self, vx, vy):
        self.axis1.trackSpeed(vx)
        self.axis2.trackSpeed(vy)

    def compose(self, x, y):
        deltax = x - self.axis1.motorBeta
        deltay = y - self.axis2.motorBeta
        angle = math.atan2(y, x)
        module = math.sqr(deltax * deltax + deltay * deltay)
        return module, angle


    def end(self):
        self.axis1.RUN = False
        self.axis2.RUN = False
        self.threadAxis1.join()
        self.threadAxis2.join()
        self.logger.critical("RUN THREAD ENDDED.Axis:%s",self.axis1.name)
        self.logger.critical("RUN THREAD ENDDED.Axis:%s",self.axis2.name)



if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s MOUNT:%(levelname)s %(message)s',level=logging.ERROR)
    m = motorHub(FullTurnSteps=200,microstepping=16,raspberry='192.168.1.11')
    m.goto(1,1,blocking=True)
    m.end()
