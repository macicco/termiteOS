#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
'''
Module Skeleton virtual class
'''

from __future__ import print_function
import time, datetime
import zmq
import json
import signal
from termiteOS.config import *


class module(object):
    def __init__(self, name, moduletype, port, parent_host, parent_port):
        print("Creating module ", name, ". Module type:", moduletype)
        self.modulename = name
        self.moduletype = moduletype
        print(name, " listen CMDs on:", port)
        self.zmqcontext = zmq.Context()
        '''
        Command explicit matrix.
        Commands starting with '.' work but are not showed.
        Also scanCMD add all methods starting with 'cmd_' as a commands
        '''
        self.CMDs={
        ".register": self.register, \
        ".deregister": self.deregister, \
        ".registrar": self.registrar, \
        ".end": self.end, \
        ".heartbeat": self.heartbeat, \
        "!": self.exeModuleCmd \
        }
        self.myHost='localhost'
        self.myCmdPort = port
        self.modules = {}
        self.RUN = True
        self.scanCMDs()
        #self.socketStream = self.zmqcontext.socket(zmq.PUB)
        #self.socketStream.bind("tcp://*:%s" % servers['zmqStreamPort'])
        self.mySocketCmd = self.zmqcontext.socket(zmq.ROUTER)
        self.mySocketCmd.bind("tcp://*:%s" % self.myCmdPort)
        if parent_port:
            #It is a slave of a hub
            print(name, " sending CMDs to:", parent_port)
            self.hasParent = True
            self.hubCmdHost = parent_host
            self.hubCmdPort = parent_port
            self.socketHUBCmd = self.zmqcontext.socket(zmq.REQ)
            self.socketHUBCmd.connect(
                "tcp://%s:%i" % (self.hubCmdHost, self.hubCmdPort))
            self.register()
        else:
            #it is the hub itself
            print("Module:", self.modulename, " is a ROOT HUB")
            self.hasParent = False
        #self.heartbeatThread = self.moduleheartbeat()
        self.CMDThread = self.zmqQueue()
        signal.signal(signal.SIGINT, self.signal_handler)

    def addCMDs(self, CMDs):
        '''add commands explicitely'''
        self.CMDs.update(CMDs)

    def scanCMDs(self):
        '''scanCMD add all methods starting with 'cmd_' as a commands'''
        raw=dir(self)
        cmd=filter(lambda x:x.startswith('cmd_'),raw)
        cmdvector={c.replace('cmd_',''):getattr(self,c) for c in cmd }
        #print('ADDED COMMANDS:',cmd)
        self.addCMDs(cmdvector)

    @threaded
    def zmqQueue(self):
        '''this thread listen and process all the CMD from other modules'''
        while self.RUN:
            try:
                address, empty, message = self.mySocketCmd.recv_multipart()
            except:
                print("Clossing mySocketCmd ZMQ socket.")
                self.mySocketCmd.close()
                break

            #  Do some 'work'
            reply = self.cmd(message)

            #  Send reply back to client to a specific client
            self.mySocketCmd.send_multipart([
                address,
                b'',
                str(reply),
            ])

        print("CMD LOOP END.")
        return

    def cmd(self, cmd):
        for c in self.CMDs.keys():
            l = len(c)
            if (cmd[:l] == c):
                arg = cmd[l:].strip()
                return self.CMDs[c](arg)
                break

        return self.cmddummy(cmd)

    def cmddummy(self, arg):
        print("DUMMY CMD:", arg)
        return

    def cmd_help(self, arg):
        string = "Base class. Do nothing"
        return string

    def cmd_ls(self,arg):
        visibleCMDs = [ c for c in self.CMDs.keys() if not c.startswith('.')]
        string = "MODULE:"+self.modulename+". TYPE:"+self.moduletype+"\n"
        string = string +"\tAvailable commands:\n"
        for cmd in visibleCMDs:
            string = string +'\t\t'+ cmd + "\n"
        return string

    def cmd_modules(self,arg):
        mod=[m for m in self.modules.keys()]
        return mod

    def cmd_tree(self, arg):
        r=[]
        for m in self.modules.keys():
                a=(m+' ls').encode("utf8")
                reply=self.exeModuleCmd(a)
                r.append(reply)
        return ''.join(r)


    def exeModuleCmd(self, arg):
        s = arg.split()
        if len(s) == 0:
            return 0
        module = s[0]
        if not (module in self.modules.keys()):
            print(module, "Not such module")
            return 0
        cmd = arg[len(module):].strip()
        print("exec:", cmd, ' on ', module, ' from ', self.modulename)
        self.modules[module]['CMDsocket'].send(cmd)
        reply = self.modules[module]['CMDsocket'].recv()
        return reply

    def registrar(self, arg):
        '''Registrar parent part'''
        r = json.loads(arg)
        module = r['module']
        self.deregister(module)
        self.modules[module] = {'name': r['module'],'host': r['host'], 'port': r['port']}
        socketCmd = self.zmqcontext.socket(zmq.REQ)
        socketCmd.connect("tcp://%s:%s" % (r['host'],r['port']))
        self.modules[module]['CMDsocket'] = socketCmd
        self.modules[module]['CMDs'] = r['CMDs']
        print(module, " sucesfully registed")
        return json.dumps({'OK': True})

    def register(self,arg=''):
        '''Call to parent registrar'''
        modulecmd = str(self.CMDs.keys())
        cmdjson=json.dumps({'module':self.modulename,\
           'host':self.myHost,\
           'port':self.myCmdPort,\
           'CMDs':modulecmd})
        cmd = '.registrar ' + cmdjson
        self.socketHUBCmd.send(cmd)
        reply = json.loads(self.socketHUBCmd.recv())
        if reply['OK']:
            print(self.modulename, " CMD PORT:", self.myCmdPort)
            print(self.modulename, " CMDs:", modulecmd)

    def deregister(self, arg):
        module = arg.strip()
        try:
            self.modules[module]['CMDsocket'].close()
            self.modules.pop(module, None)
        except:
            "Fail closing CMD socket", module
        print("DEREGISTRING: " + module)
        return "DEREGISTRING: " + module


    def end(self,arg=''):
        for module in self.modules.keys():
            print("ASK TO END:", module)
            cmd = str('.end')
            try:
                self.modules[module]['CMDsocket'].send(cmd)
                reply = self.modules[module]['CMDsocket'].recv()
                print(reply)
            except:
                print("ERROR Closing module:", module)

        if self.hasParent:
            try:
                cmd = str('.deregister ' + self.modulename)
                self.socketHUBCmd.send(cmd)
                reply = self.socketHUBCmd.recv()
                print("....", reply)
            except:
                print("Parent module is not available")
            finally:
                self.socketHUBCmd.close()

        self.RUN = False

        print("Deleting zmqcontext")
        self.zmqcontext.destroy()
        print("waiting CMDthread end")
        self.CMDThread.join()
        print("CMDthread ended")

        return self.modulename + "***ENDED***"

    def run(self):
        '''Dummy. Normaly overloaded by a child class'''
        while self.RUN:
            time.sleep(1)

    def signal_handler(self, signal, frame):
        print('You pressed Ctrl+C!')
        self.end()
        exit()

    def heartbeat(self, arg):
        '''heartbeat Parent part'''
        module = arg.strip()
        print("Received a heartBeat from a child class. Module:", module)
        return True
    
    @threaded
    def moduleheartbeat(self):
        '''Child heartbeat part'''
        time.sleep(1)
        while self.RUN:
            for module in self.modules.keys():
                cmd = str('.heartbeat ' + module)
                self.modules[module]['CMDsocket'].send(cmd)
                time.sleep(1)
                reply = self.modules[module]['CMDsocket'].recv()
                if reply:
                    print(module, "is alive")
                else:
                    print(module, "is death")


#Child class for testing
class test_class(module):
    pass


if __name__ == '__main__':
    port = 7770
    parent_host = 'localhost'
    parent_port = False
    e = test_class('test0','test', port, parent_host, parent_port)
    e.scanCMDs()
    e.run()
    exit()
