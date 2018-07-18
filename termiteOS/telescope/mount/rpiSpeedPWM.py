#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
'''
Raspberry PWM motor driver.
INTERFACE:
inherits several methods from rpiDRV8825Hut base class
- betaMotor
- pinout
- microsteps
- clutch()
- reset()
- sleep()
- set_microsteps(microsteps)
- sync(position)

Own methods:
-setSpeed (radians/seconds)
-setRPM(RPM)
-SetPoint(setpoint)
-goto() -> absolute SetPoint
-move() -> relative SetPoint
-stop()
-is
-isStopped()

'''

import math
import time, datetime
import pigpio
import logging
import termiteOS.maths.hPID as PID
import termiteOS.drivers.rpi.rpiDRV8825Hut as rpihut



#Stepper raspberry implementation
class rpiSpeedPWM(rpihut.rpiDRV8825Hut):
    def __init__(self, raspberry, driverID,microsteps, FullTurnSteps):
        super(rpiSpeedPWM, self).__init__(raspberry,driverID,microstepping=microsteps)
        self.logger = logging.getLogger(type(self).__name__)
        self.STEP_PIN = self.pinout['STEP']
        self.DIR_PIN = self.pinout['DIR']
        self.pulseDuty = 0.5
        self.maxAccel=300
        self.FullTurnSteps=FullTurnSteps*self.microsteps
        self.minMotorStep = math.pi * 2 / float(self.FullTurnSteps)
        self.SetPoint=0
        self.freq = 0
        self.Vold=0
        self.stop()
        self.RUN=True
        self.timesleep=0.1
        self.logger.debug("rpiSpeedPWM Controller created")

    def setRPM(self,rpm):
        v=rpm*2.*math.pi/60.
        self.setSpeed(v)
        self.logger.debug("RPM %f",v)

    def stop(self):
        self.pi.hardware_PWM(self.STEP_PIN, 10, 0)
        self.logger.debug("STOPPED")

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
        self.logger.debug("PWM FREQUENCY:%f",self.freq)
        return self.freq

    def rampUp(self,v,deltaT,out_min=-750,out_max=750):
        ##REVIEW
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

    def move(self,relstepcount):
        self.logger.debug("RELATIVE MOVE TO:%f",relstepcount)
        return self.goto(self.SetPoint+relstepcount)

    def goto(self,stepcount):
        self.SetPoint=stepcount
        self.logger.debug("ABSOLUTED MOVE TO:%f",stepcount)

    def run(self):
        self.T = time.time()
        pid=PID.PID(sampletime=self.timesleep,kp=0.01,ki=0.00,kd=0.00,out_min=-750,out_max=750)
        while self.RUN:
            #calculate the actual timestep
            now = time.time()
            deltaT = now - self.T
            pid.SetPoint=self.SetPoint
            feedback=self.motorBeta
            v = pid.update(feedback)
            v=self.rampUp(v,deltaT,out_min=-750,out_max=750)
            self.setRPM(v)
            time.sleep(self.timesleep)
            print("%f %f %f %f" % (pid.SetPoint,feedback,feedback-pid.SetPoint,v))
            self.logger.debug("error:%f v:%f",feedback-pid.SetPoint,v)
            self.T=now
        self.logger.critical("RUN END")

    def end(self):
        self.RUN=False
        self.runThread.join()
        self.logger.critical("RUN THREAD ENDDED.")
        exit(0)        



if __name__ == '__main__':
        logging.basicConfig(format='%(asctime)s PWMspeed:%(levelname)s %(message)s',level=logging.DEBUG)
        axis=rpiSpeedPWM('192.168.1.11',0,16,200)
        axis.goto(160000)
        axis.run()
        print(axis.isStopped())
        print(axis.motorBeta)

