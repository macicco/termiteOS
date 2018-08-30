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



class rpiServoHat:
        def __init__(self):
                self.pwm = Adafruit_PCA9685.PCA9685()
                # Set frequency to 60hz, good for servos.
                self.pwmFreq=60
                self.pwm.set_pwm_freq(self.pwmFreq)
                # Alternatively specify a different address and/or bus:
                #pwm = Adafruit_PCA9685.PCA9685(address=0x41, busnum=2)
                # Configure min and max servo pulse lengths
                servo_min = 150  # Min pulse length out of 4096
                servo_max = 600  # Max pulse length out of 4096

        # Helper function to make setting a servo pulse width simpler.
        def set_servo_pulse(channel, pulse):
            pulse_length = 1000000    # 1,000,000 us per second
            pulse_length //= self.pwmFreq       
            pulse_length //= 4096     # 12 bits of resolution
            print('{0}us per bit'.format(pulse_length))
            pulse *= 1000
            pulse //= pulse_length
            pwm.set_pwm(channel, 0, pulse)


if __name__ == '__main__':
        print('Moving servo on channel 0, press Ctrl-C to quit...')
        while True:
            # Move servo on channel O between extremes.
            pwm.set_pwm(0, 0, servo_min)
            time.sleep(1)
            pwm.set_pwm(0, 0, servo_max)
            time.sleep(1)
