#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
'''
Raspberry PWM motor driver.

'''

import math
import time, datetime
import pigpio
import termiteOS.maths.hPID as PID
import termiteOS.drivers.rpi.rpiDRV8825Hut as rpihut


#Stepper raspberry implementation
class rpiSpeedPWM(rpihut.rpiDRV8825Hut):
    def __init__(self, raspberry, driverID,microsteps, FullTurnSteps):
        super(rpiSpeedPWM, self).__init__(raspberry,driverID,microstepping=microsteps)
        #self.set_microsteps(microsteps)
        self.STEP_PIN = self.pinout['STEP']
        self.DIR_PIN = self.pinout['DIR']
        self.FullTurnSteps=FullTurnSteps*self.microsteps
        self.pulseWidth = 1. / float(self.maxPPS)
        self.pulseDuty = 0.5
        self.minMotorStep = math.pi * 2 / float(self.FullTurnSteps)
        self.vmax = self.minMotorStep / self.pulseWidth
        self.freq = 0
        self.Vold=0
        self.stop()


    def setRPM(self,rpm):
            v=rpm*2.*math.pi/60.
            self.setSpeed(v)

    def stop(self):
            self.pi.hardware_PWM(self.STEP_PIN, 10, 0)


    def isStopped(self):
                PWMstate =  (self.pi.get_PWM_dutycycle(self.pinout['STEP']) == 0)
                return PWMstate

    def setSpeed(self, v):
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
            self.pi.hardware_PWM(self.STEP_PIN, self.freq,self.pulseDuty * 1000000)

            return self.freq

    def rampUp(self,v):
        maxDeltaV=100
        deltaV=v-self.Vold
        if abs(deltaV)>=maxDeltaV:
            v=self.Vold+math.copysign(maxDeltaV, deltaV)
        self.Vold=v
        return v
       
    def goto(self,count):
        pid=PID.PID(sampletime=0.2,kp=0.01,ki=0.01,kd=0.00,out_min=-750,out_max=750)
        pid.SetPoint=count
        while True:
            feedback=self.motorBeta
            pid.SetPoint+=10000
            output = pid.update(feedback)
            v=output
            v=self.rampUp(v)
            self.setRPM(v)
            time.sleep(0.2)
            print(pid.SetPoint,feedback,feedback-pid.SetPoint,v)



if __name__ == '__main__':
        axis=rpiSpeedPWM('192.168.1.11',0,32,200)
        axis.goto(100000)
        axis.setRPM(100)
        time.sleep(1)
        axis.setRPM(400)
        time.sleep(1)
        axis.setRPM(600)
        time.sleep(1)
        axis.setRPM(750)
        time.sleep(5)
        axis.setRPM(100)
        time.sleep(1)
        axis.stop()
        print(axis.isStopped())

        print(axis.motorBeta)

