#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
# Adapted from: https://github.com/hirschmann/pid-autotune/blob/master/pid.py
from __future__ import print_function
from time import time
from time import sleep
import logging

class PID(object):
    """A proportional-integral-derivative controller.
    Args:
        sampletime (float): The interval between calc() calls.
        kp (float): Proportional coefficient.
        ki (float): Integral coefficient.
        kd (float): Derivative coefficient.
        out_min (float): Lower output limit.
        out_max (float): Upper output limit.
        time (function): A function which returns the current time in seconds.
    """

    def __init__(self, sampletime, kp, ki, kd, out_min=float('-inf'),
                 out_max=float('inf'), time=time):
        if kp is None:
            raise ValueError('kp must be specified')
        if ki is None:
            raise ValueError('ki must be specified')
        if kd is None:
            raise ValueError('kd must be specified')
        if sampletime <= 0:
            raise ValueError('sampletime must be greater than 0')
        if out_min >= out_max:
            raise ValueError('out_min must be less than out_max')

        self._logger = logging.getLogger(type(self).__name__)
        self._Kp = kp
        self._Ki = ki * sampletime
        self._Kd = kd / sampletime
        self._sampletime = sampletime * 1000
        self._out_min = out_min
        self._out_max = out_max
        self._integral = 0
        self._last_input = 0
        self._last_output = 0
        self._last_calc_timestamp = 0
        self._time = time
        self.SetPoint=0

    def reset(self):
        self._integral = 0
        self._last_input = 0
        self._last_output = 0
        self._last_calc_timestamp = 0

    def update(self, input_val):
        """Adjusts and holds the given setpoint.
        Args:
            input_val (float): The input value.
            setpoint (float): The target value.
        Returns:
            A value between `out_min` and `out_max`.
        """
        setpoint=self.SetPoint
        now = self._time() * 1000


        if (now - self._last_calc_timestamp) < self._sampletime:
            return self._last_output

        # Compute all the working error variables
        error = setpoint - input_val
        input_diff = input_val - self._last_input

        # In order to prevent windup, only integrate if the process is not saturated
        if self._last_output < self._out_max and self._last_output > self._out_min:
            self._integral += self._Ki * error
            self._integral = min(self._integral, self._out_max)
            self._integral = max(self._integral, self._out_min)

        p = self._Kp * error
        i = self._integral
        d = -(self._Kd * input_diff)

        # Compute PID Output
        self._last_output = p + i + d
        self._last_output = min(self._last_output, self._out_max)
        self._last_output = max(self._last_output, self._out_min)

        # Log some debug info
        self._logger.debug('P:{0} I:{1} D:{2} output:{3}'.format(p,i,d,self._last_output))

        # Remember some variables for next time
        self._last_input = input_val
        self._last_calc_timestamp = now
        return self._last_output

if __name__ == '__main__':
        END=50
        feedback=0
        pid = PID(sampletime=0.1,kp=1.,ki=1,kd=0.005)
        for i in range(1, END):
            output = pid.update(feedback)
            if pid.SetPoint > 0:
                feedback += (output - (1/i))
            if i>9:
                pid.SetPoint = 1
            sleep(0.2)
            print(i,pid.SetPoint,feedback)
