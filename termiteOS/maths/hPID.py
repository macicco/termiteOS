#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
# Adapted from: https://github.com/hirschmann/pid-autotune/blob/master/pid.py
'''
Adapted from: https://github.com/hirschmann/pid-autotune/blob/master/pid.py

.. image:: https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/PID_en.svg/971px-PID_en.svg.png
   :width: 800px
   :scale: 50 %
   :alt: DRV8825Hat
   :align: center


'''
from __future__ import print_function
from time import time
from time import sleep
import math
import logging

class PID(object):
    """A proportional-integral-derivative controller.
           Named Args:
                :param timestep (float): The min interval between update() calls.
                :param acceleration (float): max accelerarion in RPM/s (motor axis).
                :param kp (float): Proportional coefficient.
                :param ki (float): Integral coefficient.
                :param kd (float): Derivative coefficient.
                :param out_min (float): Lower output limit in RPM  (motor axis).
                :param out_max (float): Upper output limit in RPM  (motor axis).

                :returns: New output
    """
    def __init__(self, timestep=0.1,acceleration=300, kp=0, ki=0, kd=0, out_min=float('-inf'),
                 out_max=float('inf')):
        self._logger = logging.getLogger(type(self).__name__)
        self._Kp = kp
        self._Ki = ki * timestep
        self._Kd = kd / timestep
        self._timestep = timestep * 1000
        self._acceleration=acceleration
        self._out_min = out_min
        self._out_max = out_max
        self._integral = 0
        self._last_input = 0
        self._last_output = 0
        self._last_calc_timestamp = 0



    def reset(self):
        '''Reset internal values. Forget the history'''
        self._integral = 0
        self._last_input = 0
        self._last_output = 0
        self._last_calc_timestamp = 0

    def update(self,setpoint, feedback):
        """
        Adjusts and holds the given setpoint.
        Args:
            :param setpoint (float): The target value. 
            :param feedback (float): The feedback value.
            :returns: A value between `out_min` and `out_max`.
        """

        now = time() * 1000
        deltaT =now - self._last_calc_timestamp
        if deltaT < self._timestep:
            return self._last_output

        # Compute all the working error variables
        error = setpoint - feedback
        
        input_diff = feedback - self._last_input

        # In order to prevent windup, only integrate if the process is not saturated
        if self._last_output < self._out_max and self._last_output > self._out_min:
            self._integral += self._Ki * error
            self._integral = min(self._integral, self._out_max)
            self._integral = max(self._integral, self._out_min)

        p = self._Kp * error
        i = self._integral
        d = -(self._Kd * input_diff)

        # Compute PID Output
        pid = p + i + d

        #Limit acceleration
        deltaV=pid-self._last_output
        self._logger.debug('pid:{0} deltaV:{1} deltaT:{2}'.format(pid,deltaV,deltaT/1000))
        if abs(deltaV) >= self._acceleration*deltaT/1000:
                pid = self._last_output + math.copysign(self._acceleration*deltaT/1000,deltaV)

        #Limite Output
        pid = min(pid, self._out_max)
        pid = max(pid, self._out_min)

        # Log some debug info
        self._logger.debug('P:{0} I:{1} D:{2} output:{3}'.format(p,i,d,pid))

        # Remember some variables for next time
        self._last_output = pid
        self._last_input = feedback
        self._last_calc_timestamp = now
        return self._last_output

if __name__ == '__main__':
        END=50
        feedback=0
        SetPoint=0
        pid = PID(timestep=0.1,kp=1.,ki=1,kd=0.005)
        for i in range(1, END):
            output = pid.update(SetPoint,feedback)
            if SetPoint > 0:
                feedback += (output - (1/i))
            if i>9:
                SetPoint = 1
            sleep(0.2)
            print(i,SetPoint,feedback)
