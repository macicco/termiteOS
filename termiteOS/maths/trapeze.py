#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
# Adapted from: https://github.com/hirschmann/pid-autotune/blob/master/pid.py
'''
Calculation of speed to target following a trapeze
'''

from __future__ import print_function
from time import time
from time import sleep
import math
import logging

class trapeze(object):
    """A proportional-integral-derivative controller.
    Args:
        :param timestep (float): The min interval between update() calls.
        :param acceleration (float): Max acceleration in RPM/s (motor axis).
        :param out_min (float): Lower output limit in RPM (motor axis).
        :param out_max (float): Upper output limit in RPM (motor axis).
        :returns: New output
    """
    def __init__(self, timestep=0.1, acceleration=1, out_min=float('-inf'),
                 out_max=float('inf')):

        self._logger = logging.getLogger(type(self).__name__)
        self._acceleration=acceleration
        self._timestep = timestep 
        self._out_min = out_min
        self._out_max = out_max
        self._last_input = 0
        self._last_output = 0
        self._last_calc_timestamp = 0
        self.SetPoint=0

    def reset(self):
        '''Reset internal values. Forget the history'''
        self._last_input = 0
        self._last_output = 0
        self._last_calc_timestamp = 0

    def update(self, setpoint,feedback):
        """
        Adjusts and holds the given setpoint.
        Args:
            :param setpoint (float): The target value.
            :param input_val (float): The feedback  value.
            :returns: A value between `out_min` and `out_max`.
        """

        now = time() 
        deltaT=now - self._last_calc_timestamp
        if (deltaT) < self._timestep:
            return self._last_output

        # Compute all error variables
        error = (setpoint - feedback)
        v= self._last_output
        sign = math.copysign(1, error)
        v_sign = math.copysign(1, v)
        beta_slope = (v * v) / (2 * self._acceleration*deltaT)

        #Change in direction
        if sign != v_sign:
            a = self._acceleration * sign

        #check if it is time to deccelerate
        if abs(error) - beta_slope <= 0:
            a = -self._acceleration * sign
        else:
            a = self._acceleration * sign

        #Already at max speed
        if v>=self._out_max or v<=self._out_min:
            a=0

        #no error
        if error==0:
                a=0


        # Compute Output
        self._last_output = self._last_output + a * self._timestep

        print(setpoint,feedback,error,v,sign,v_sign,a,self._last_output)

        #limit the output       
        self._last_output = min(self._last_output, self._out_max)
        self._last_output = max(self._last_output, self._out_min)

        # Log some debug info
        self._logger.debug('output:{}'.format(self._last_output))

        # Remember some variables for next time
        self._last_input = feedback
        self._last_calc_timestamp = now
        return self._last_output

if __name__ == '__main__':
        END=500
        feedback=0
        SetPoint = 0
        timestep=0.1
        pid = trapeze(timestep=timestep,acceleration=1)
        for i in range(1, END):
            output = pid.update(SetPoint,feedback)
            feedback += output*timestep
            if i>25:
                SetPoint = 10
            sleep(timestep)
            #print(i,SetPoint,feedback)
