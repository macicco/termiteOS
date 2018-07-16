#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
from termiteOS.config import *

class mount:
    def __init__(self):
        simulation = False
        import pigpio
        pi = pigpio.pi(servers['pigpio'])
        if simulation:
            self.axis1 = axis('RA')
            self.axis2 = axis('DEC')
        else:
            ''' RASPBERRY B+ PWM PINOUT
			12  PWM channel 0  All models but A and B
			13  PWM channel 1  All models but A and B
			18  PWM channel 0  All models
			19  PWM channel 1  All models but A and B
			CHOSE DIFERENT CHANNELS FOR RA AND DEC !!
   	    '''
   

            self.axis1 = AxisDriver('RA', 0)
            self.axis2 = AxisDriver('DEC',1)
        self.run()

    def run(self):
        self.threadAxis1=self.axis1.run()
        self.threadAxis2=self.axis2.run()

    def slew(self, x, y, blocking=False):
        self.setVmax(x, y)
        self.axis1.slew(x, blocking)
        self.axis2.slew(y, blocking)

    def sync(self, x, y):
        self.axis1.sync(x)
        self.axis2.sync(y)

    def slewend(self):
        return (self.axis1.slewend and self.axis2.slewend)

    def stopSlew(self):
        self.axis1.slew(self.axis1.beta)
        self.axis2.slew(self.axis2.beta)

    def track(self, vx, vy):
        self.axis1.track(vx)
        self.axis2.track(vy)

    def trackSpeed(self, vx, vy):
        self.axis1.vtracking = ephem.degrees(vx)
        self.axis2.vtracking = ephem.degrees(vy)

    def compose(self, x, y):
        deltax = x - self.axis1.beta
        deltay = y - self.axis2.beta
        angle = math.atan2(y, x)
        module = math.sqr(deltax * deltax + deltay * deltay)
        return module, angle

    def setVmax(self, x, y):
        deltax = abs(x - self.axis1.beta)
        deltay = abs(y - self.axis2.beta)
        self.axis1._vmax = float(self.axis1.vmax)
        self.axis2._vmax = float(self.axis2.vmax)
        return
        if deltax == 0 or deltay == 0:
            return
        if deltax > deltay:
            self.axis2._vmax = self.axis2.vmax * deltay / deltax
        else:
            self.axis1._vmax = self.axis1.vmax * deltax / deltay
        #print "VAXIS:",self.axis1._vmax,self.axis2._vmax
        return

    def coords(self):
        print time.time()-self.T0,self.axis1.timestep,self.axis2.timestep,self.axis1.beta, \
         self.axis2.beta,self.axis1.v,self.axis2.v,self.axis1.a,self.axis2.a

    def end(self):
        self.axis1.RUN = False
        self.axis2.RUN = False
        self.threadAxis1.join()
        self.threadAxis2.join()



if __name__ == '__main__':
    m0=rpihut.rpiDRV8825Hut(servers['pigpio'],0)
    m1=rpihut.rpiDRV8825Hut(servers['pigpio'],0)

    m = mount()
    vRA = ephem.degrees('-00:00:15')
    m.trackSpeed(vRA, 0)
    RA = ephem.hours('03:00:00')
    DEC = ephem.degrees('15:00:00')
    m.slew(RA, DEC)
    t = 0
    while t < 15:
        t = t + m.axis1.timestep
        time.sleep(m.axis1.timestep)
        #m.coords()
    RA = ephem.hours('01:00:00')
    DEC = ephem.degrees('-15:00:00')
    m.slew(RA, DEC)
    t = 0
    while t < 15:
        t = t + m.axis1.timestep
        time.sleep(m.axis1.timestep)
        #m.coords()
    m.end()
