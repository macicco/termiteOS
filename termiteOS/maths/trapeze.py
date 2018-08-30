#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
'''
Calculation of speed to target following a trapeze
'''

from __future__ import print_function
from time import time
from time import sleep
import math
import logging



class trapeze(object):
    """A ramp controller. Ramp speed until vmax.
    Args:
        :param timestep (float): The min interval between update() calls.
        :param acceleration (float): Max acceleration in RPM/s (motor axis).
        :param min_error (float): Min error threshold.
        :param out_min (float): Lower output limit in RPM (motor axis).
        :param out_max (float): Upper output limit in RPM (motor axis).
        :returns: New output
    """
    def __init__(self, timestep=0.1, acceleration=1,min_error=1, out_min=float('-inf'),
                 out_max=float('inf')):

        self._logger = logging.getLogger(type(self).__name__)
        self._acceleration=acceleration
        self._min_error=min_error
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

        actual_acceleration=self._acceleration
        #Slow down for small displacements
        #TBD

        e_sign = math.copysign(1, error)
        v= self._last_output
        v_sign = math.copysign(1, v)
        beta_slope = (v * v ) / (2 * actual_acceleration)
        #print(beta_slope,error)

        #check if it is time to deccelerate
        if abs(error) <= beta_slope :
            a = -actual_acceleration * e_sign
        else:
            a = actual_acceleration * e_sign

        #Change in direction
        if (e_sign * v_sign) == -1:
            a = actual_acceleration * e_sign


        # Compute Output
        self._last_output = self._last_output + a * deltaT

        #no error
        if abs(error)<=self._min_error:
                self._last_output = 0

        #limit the output       
        self._last_output = min(self._last_output, self._out_max)
        self._last_output = max(self._last_output, self._out_min)

        # Log some debug info
        self._logger.debug('output:{0} beta_slope:{1}'.format(self._last_output,beta_slope))

        # Remember some variables for next time
        self._last_input = feedback
        self._last_calc_timestamp = now
        return self._last_output

if __name__ == '__main__':
        END=300
        feedback=0
        SetPoint = 0
        timestep=0.1
        factor= 100 * 16 * 200  
        pid = trapeze(timestep=timestep,acceleration=300*factor/60,out_max=750*factor/60,out_min=-750*factor/60)
        for i in range(1, END):
            output = pid.update(SetPoint,feedback)
            feedback +=  output*timestep
            if i>=5:
                SetPoint = 5 * factor
            if i>=150:
                SetPoint = 0 * factor
            sleep(timestep)
            print(i,SetPoint,feedback,output)
