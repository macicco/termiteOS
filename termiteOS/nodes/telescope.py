#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
'''
ENGINE
'''
from __future__ import print_function
import ephem
import time, datetime
import math
import json
import logging
from termiteOS.config import *
from termiteOS.drivers.motorHub import motorHub as motorHub
import termiteOS.nodeSkull as nodeSkull


class telescope(nodeSkull.node):
    def __init__(self, name, port, parent_host, parent_port):
        super(telescope, self).__init__(name, 'telescope', port, parent_host, parent_port)
        CMDs={
        chr(6):self.cmd_ack,  \
        ":info": self.cmd_info,  \
          ":FirmWareDate": self.cmd_firware_date,  \
          ":GVF": self.cmd_firware_ver,  \
          ":V": self.cmd_firware_ver,  \
          ":GVD": self.cmd_firware_date,  \
          ":GC": self.cmd_getLocalDate,  \
          ":GL": self.cmd_getLocalTime,  \
          ":GS": self.cmd_getSideralTime,  \
          ":Sr": self.cmd_setTargetRA,  \
          ":Sd": self.cmd_setTargetDEC,  \
          ":MS": self.cmd_slew,  \
          ":Q":  self.cmd_stopSlew,  \
          ":Gr": self.cmd_getTargetRA,  \
          ":Gd": self.cmd_getTargetDEC,  \
          ":GR": self.cmd_getTelescopeRA,  \
          ":GD": self.cmd_getTelescopeDEC,  \
          ":RS": self.cmd_setMaxSlewRate,  \
          ":RM": self.cmd_slewRate,  \
          ":Me": self.cmd_pulseE,  \
          ":Mw": self.cmd_pulseW,  \
          ":Mn": self.cmd_pulseN,  \
          ":Ms": self.cmd_pulseS,  \
          ":CM": self.cmd_align2target,  \
          "@getObserver": self.getObserver, \
          "@getGear": self.getGear, \
          "@getRA": self.getRA, \
          "@getDEC": self.getDEC, \
          "@setTrackSpeed": self.setTrackSpeed, \
          "@values": self.values
        }
        self.m = motorHub(microstepping=16,raspberry='192.168.1.11')
        self.valuesmsg = {}
        self.addCMDs(CMDs)
        self.observerInit()
        self.targetRA = ephem.hours(0)
        self.targetDEC = ephem.degrees(0)
        ra = ephem.hours(self.observer.sidereal_time())
        dec = ephem.degrees(0)
        star = ephem.FixedBody(ra, dec, observer=self.observer, epoch='2016.4')
        star.compute(self.observer)
        self.RA = star.ra
        self.DEC = star.dec
        self.alt = star.alt
        self.az = star.az

        self.pulseStep = ephem.degrees('00:00:01')
        a = ephem.degrees('00:20:00')

        vRA = -ephem.hours("00:00:01")
        vDEC = ephem.degrees("00:00:00")
        self.m.setTrackSpeed(vRA, vDEC)

    def observerInit(self):
        self.observer = ephem.Observer()
        self.observer.lat = here['lat'] * math.pi / 180.
        self.observer.lon = here['lon'] * math.pi / 180.
        self.observer.horizon = ephem.degrees(here['horizon'])
        self.observer.elev = here['elev']
        self.observer.temp = here['temp']
        self.observer.compute_pressure()
        logging.info("Observer Lat: %s",self.observer.lat)

    def getObserver(self, arg):
        observer = {'lat':str(ephem.degrees(self.observer.lat)),'lon':str(ephem.degrees(self.observer.lon)),\
          'horizon':str(ephem.degrees(self.observer.horizon)),\
          'elev':self.observer.elev,'temp':self.observer.temp}
        return json.dumps(observer)

    def getGear(self, arg):
        data = {'acceleration':engine['acceleration'],\
          'pointError':str(ephem.degrees(self.m.axis1.minMotorStep)),\
          'vmax':str(ephem.degrees(self.m.axis1.vmax)),\
          'FullTurnSteps':self.m.axis1.FullTurnSteps}
        logging.info("getGear:%s",data)
        return json.dumps(data)

    def setTrackSpeed(self, arg):
        c = arg.split()
        vRA = ephem.degrees(c[0])
        vDEC = ephem.degrees(c[1])
        self.m.setTrackSpeed(vRA, vDEC)

    def altAz_of(self, ra, dec):
        p = ephem.FixedBody()
        p._ra, p._dec = ra, dec
        p.compute(self.observer)
        return (p.alt, p.az)

    def run(self):
        while self.RUN:
            time.sleep(0.1)
            #update
            ra = self.getRA('')
            dec = self.getDEC('')
            #np=ephem.Equatorial(ra,dec,epoch=ephem.now()) #!bad
            self.alt, self.az = self.altAz_of(ra, dec)
            '''
            self.valuesmsg = {'time':str(self.observer.date),'LST':str(self.sideral),\
             'RA':str(self.RA),'DEC':str(self.DEC),\
             'ALT':str(self.alt),'AZ':str(self.az),\
             'targetRA':str(self.targetRA),'targetDEC':str(self.targetDEC),\
             'speedRA':str(self.m.axis1.v),'speedDEC':str(self.m.axis2.v),\
             'trackingSpeedRA':str(self.m.axis1._trackSpeed),'trackingSpeedDEC':str(self.m.axis2._trackSpeed),\
             'slewendRA':str(self.m.axis1.gotoEnd),'slewendDEC':str(self.m.axis2.gotoEnd)\
             }
            '''
            #self.socketStream.send(mogrify('values',msg))
            if False:
                if self.alt <= ephem.degrees('10:00:00'):
                    self.cmd_stopSlew('')
        logging.info("ALL MOTORS STOPPED")

    def values(self, arg):
        return mogrify('values', self.valuesmsg)


    def cmd_ack(self, arg):
        return "P"

    def cmd_info(self, arg):
        return "pyLX200 driver#"

    def cmd_firware_date(self, arg):
        return "01/02/2016#"

    def cmd_firware_ver(self, arg):
        return "LX200 Master. Python mount controler. Ver 0.1#"

    def cmd_getLocalDate(self, arg):
        return time.strftime("%m/%d/%y") + '#'

    def cmd_getLocalTime(self, arg):
        return time.strftime("%H:%M:%S") + '#'

    def cmd_getSideralTime(self, arg):
        sideralTime = self.observer.sidereal_time()
        return str(self.sideralTime) + '#'

    def cmd_getTargetRA(self, arg):
        return str(self.targetRA) + '#'

    def cmd_getTargetDEC(self, arg):
        return str(self.targetDEC) + '#'

    def cmd_setTargetRA(self, arg):
        self.targetRA = ephem.hours(arg)
        return 1

    def cmd_setTargetDEC(self, arg):
        arg = arg.replace('*', ':')
        arg = arg.replace(chr(223), ':')
        arg = arg.replace('’', ':')
        self.targetDEC = ephem.degrees(arg)
        return 1

    def cmd_align2target(self, arg):
        ra = self.hourAngle(self.targetRA)
        self.m.sync(ra, self.targetDEC)
        return "target#"

    def cmd_slew(self, arg):
        #return values 0==OK, 1 == below Horizon
        alt, az = self.altAz_of(self.targetRA, self.targetDEC)
        if alt <= self.observer.horizon and engine['overhorizon']:
            logging.info("Not slewing: Below horizon")
            r = '1'
        else:
            ra = self.hourAngle(self.targetRA)
            logging.info("slewing from:%s %s to %s %s", self.RA, self.DEC, self.targetRA, self.targetDEC)
            self.m.goto(ra, self.targetDEC)
            r = '0'
        return r + "#"

    def hourAngle(self, ra):
        self.observer.date = ephem.now()
        self.sideral = self.observer.sidereal_time()
        ra_ = ephem.hours(ra - self.sideral).znorm
        if ra_ == ephem.hours("24:00:00"):
            ra = ephem.hours("00:00:00")
        return ra_

    def cmd_stopSlew(self, arg):
        self.m.stop()
        return 1

    def track(self):
        vRA = ephem.hours("00:00:01")
        vDEC = ephem.degrees("00:00:00")
        self.m.setSpeed(vRA, vDEC)
        return

    #Update RA primitive
    def getRA(self, arg):
        self.observer.date = ephem.Date(datetime.datetime.utcnow())
        self.sideral = self.observer.sidereal_time()
        beta = float(self.m.axis1.pos)
        ra = ephem.hours(self.sideral + beta).norm
        if ra == ephem.hours("24:00:00"):
            ra = ephem.hours("00:00:00")
        self.RA = ra
        return self.RA

    #Update DEC primitive
    def getDEC(self, arg):
        beta = float(self.m.axis2.pos) 
        #beta=self.m.axis2.beta
        sign = math.copysign(1, beta)
        self.DEC = ephem.degrees(beta)
        return self.DEC

    def cmd_getTelescopeRA(self, arg):
        self.getRA('')
        data = str(self.RA)
        H, M, S = data.split(':')
        H = int(H)
        M = int(M)
        S = round(float(S))
        d = "%02d:%02d:%02d" % (H, M, S)
        return d + '#'

    def cmd_getTelescopeDEC(self, arg):
        self.getDEC('')
        data = str(self.DEC)
        D, M, S = data.split(':')
        if D[0] == '-':
            sign = '-'
        else:
            sign = '+'
        D = int(D)
        M = int(M)
        S = round(float(S))
        d = "%s%02d*%02d:%02d" % (sign, abs(D), M, S)
        d = d.replace('*', chr(223))
        return d + '#'

    def cmd_pulseE(self, arg):
        self.targetRA = self.targetRA + self.pulseStep
        self.cmd_slew('')

    def cmd_pulseW(self, arg):
        self.targetRA = self.targetRA - self.pulseStep
        self.cmd_slew('')

    def cmd_pulseN(self, arg):
        self.targetDEC = self.targetDEC + self.pulseStep
        self.cmd_slew('')

    def cmd_pulseS(self, arg):
        self.targetDEC = self.targetDEC - self.pulseStep
        self.cmd_slew('')

    def cmd_setMaxSlewRate(self, arg):
        return 1

    def cmd_slewRate(self, arg):
        return 1

    def end(self, arg=''):
        self.m.end()
        super(telescope, self).end()


def runtelescope(name, port, parent_host='', parent_port=False):
    ''' **ENTRYPOINT** calling this fuction start the node'''
    s = telescope(name, port, parent_host, parent_port)
    try:
        s.run()
    except:
        s.end()


if __name__ == '__main__':
    runtelescope('TELESCOPE0', 5000)
