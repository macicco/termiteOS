#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
'''
Raspberry servo motor driver.
Used with Adafruit_PCA9685 raspberry Hat
'''

from __future__ import division
import time


import Adafruit_PCA9685
pwmHat = Adafruit_PCA9685.PCA9685()


class rpiServoHat:
        def __init__(self,params={'low':500,'high':2000}):
                self.high_pulse=params['high']
                self.low_pulse=params['low']
                self.FullTurnPulses=self.high_pulse-self.low_pulse
                self.pwm = pwmHat
                # Set frequency to 60hz, good for servos.
                self.pwmFreq=50
                self.pwm.set_pwm_freq(self.pwmFreq)
                self.dir=1
                self.motorBeta = 0
                # Alternatively specify a different address and/or bus:
                #pwm = Adafruit_PCA9685.PCA9685(address=0x41, busnum=2)
                # Configure min and max servo pulse lengths

        # Helper function to make setting a servo pulse width simpler.
        def set_servo_pulse(self,channel, pulse):
                pulse_length = 1000000    # 1,000,000 us per second
                pulse_length //= self.pwmFreq       
                pulse_length //= 4096     # 12 bits of resolution
                #print('{0}us per bit'.format(pulse_length))
                #pulse *= 1000
                print(channel,pulse)
                pulse //= pulse_length
                self.pwm.set_pwm(channel, 0, pulse)

        def set_pwm(self,channel,on,off):
                self.pwm.set_pwm(channel,on,off)


if __name__ == '__main__':
        print('Moving servo on channel 0, press Ctrl-C to quit...')
        servos={0:{'low':1000,'high':2000},3:{'low':1000,'high':2000},4:{'low':1000,'high':2000}}
        servo=rpiServoHat()
        if True:
                s=0
                for p in range(servos[s]['low'],servos[s]['high']):
                    now=time.time()
                    servo.set_servo_pulse(s,p)                
                    time.sleep(0.001)
                    print(time.time()-now)
                servo.set_servo_pulse(s,servos[s]['low'])
        laptime=1
        while True:
            # Move servo on channel O between extremes.
            if laptime >0.1:
                    laptime-=0.1
            else:
                    laptime+=0.1
            for s in servos.keys():
                    center=int((servos[s]['low']+servos[s]['high'])/2)
                    servo.set_servo_pulse(s,center)
                    time.sleep(laptime)
                    servo.set_servo_pulse(s,servos[s]['low'])
                    time.sleep(laptime)
                    servo.set_servo_pulse(s,center)
                    time.sleep(laptime)
                    servo.set_servo_pulse(s,servos[s]['high'])
                    time.sleep(laptime)

