#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
from __future__ import print_function
import logging
import time
from termiteOS.telescope.mount import rpiSpeedPWM as AxisDriver


class gears:
        def __init__(self,ratio):
                self.ratio=ratio

        def go(self,value):
                return value*self.ratio

        def back(self,value):
                return value/self.ratio


if __name__ == '__main__':
        logging.basicConfig(format='%(asctime)s MOUNT:%(levelname)s %(message)s',level=logging.ERROR)
        g0=gears(0.1)
        v=10
        for i in range(100):
                g0=gears(1./(1+i))
                print("ratio=%f. Convert and back %f: %f --> %f --> %f" % (g0.ratio,v,g0.go(v),g0.back(g0.go(v)),g0.go(g0.back(g0.go(v)))))
        
