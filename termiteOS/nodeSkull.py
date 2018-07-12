#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
'''
node Skeleton virtual class
'''

from __future__ import print_function
import time, datetime
import zmq
import json
import signal
from termiteOS.config import *


class node(object):
    def __init__(self, name, nodetype, port, parent_host, parent_port):
        print("Creating node ", name, ". node type:", nodetype)
        self.nodename = name
        self.nodetype = nodetype
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
        "!": self.exenodeCmd \
        }
        self.myHost='localhost'
        self.myCmdPort = port
        self.nodes = {}
        self.RUN = True
        self.scanCMDs()
        #self.socketStream = self.zmqcontext.socket(zmq.PUB)
        #self.socketStream.bind("tcp://*:%s" % servers['zmqStreamPort'])
        self.myCmdSocket = self.zmqcontext.socket(zmq.ROUTER)
        self.myCmdSocket.bind("tcp://*:%s" % self.myCmdPort)
        if parent_port:
            #It is a slave of a hub
            print(name, " sending CMDs to:", parent_port)
            self.hasParent = True
            self.hubCmdHost = parent_host
            self.hubCmdPort = parent_port
            self.ParentCmdSocket = self.zmqcontext.socket(zmq.REQ)
            self.ParentCmdSocket.connect(
                "tcp://%s:%i" % (self.hubCmdHost, self.hubCmdPort))
            self.register()
        else:
            #it is the hub itself
            print("node:", self.nodename, " is a ROOT HUB")
            self.hasParent = False
        #self.heartbeatThread = self.nodeheartbeat()
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
        '''this thread listen and process all the CMD from other nodes'''
        while self.RUN:
            if True:
                try:
                        address, empty, message = self.myCmdSocket.recv_multipart()
                except:
                        self.myCmdSocket.close()
                        break

                '''
                Special case for .end command.
                Calling end() close all sockets so we have to answer before.
                '''
                if message == '.end':
                        reply='Last message from '+self.nodename+'. Closing socket'
                        self.myCmdSocket.send_multipart([
                                address,
                                b'',
                                str(reply),
                                ])
                        #self.myCmdSocket.close()
                        self.end()
                        break
                else:
                        #  Do some 'work'
                        reply = self.cmd(message)

                        #  Send reply back to a specific client
                        self.myCmdSocket.send_multipart([
                                address,
                                b'',
                                str(reply),
                                ])
            '''
            try:
                address, empty, message = self.myCmdSocket.recv_multipart()

                if message == '.end':
                        reply='Last message from '+self.nodename+'. Closing socket'
                        self.myCmdSocket.send_multipart([
                                address,
                                b'',
                                str(reply),
                                ])
                        self.myCmdSocket.close()
                        self.end()
                        print("CMD LOOP END.")
                        return
                else:
                        #  Do some 'work'
                        reply = self.cmd(message)

                        #  Send reply back to a specific client
                        self.myCmdSocket.send_multipart([
                                address,
                                b'',
                                str(reply),
                                ])
            except:
                print("Clossing"+self.nodename+ " myCmdSocket ZMQ socket.")
                self.myCmdSocket.close()
                break
            '''
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
        string = "node:"+self.nodename+". TYPE:"+self.nodetype+"\n"
        string = string +"\tAvailable commands:\n"
        for cmd in visibleCMDs:
            string = string +'\t\t'+ cmd + "\n"
        return string

    def cmd_nodes(self,arg):
        mod=[m for m in self.nodes.keys()]
        return mod

    def cmd_tree(self, arg):
        r=[]
        for m in self.nodes.keys():
                a=(m+' ls').encode("utf8")
                reply=self.exenodeCmd(a)
                r.append(reply)
        return ''.join(r)


    def exenodeCmd(self, arg):
        s = arg.split()
        if len(s) == 0:
            return 0
        node = s[0]
        if not (node in self.nodes.keys()):
            print(node, "Not such node")
            return 0
        cmd = arg[len(node):].strip()
        print("exec:", cmd, ' on ', node, ' from ', self.nodename)
        self.nodes[node]['CMDsocket'].send(cmd)
        reply = self.nodes[node]['CMDsocket'].recv()
        return reply

    def registrar(self, arg):
        '''Registrar parent part'''
        r = json.loads(arg)
        node = r['node']
        self.deregister(node)
        self.nodes[node] = {'name': r['node'],'host': r['host'], 'port': r['port']}
        socketCmd = self.zmqcontext.socket(zmq.REQ)
        socketCmd.connect("tcp://%s:%s" % (r['host'],r['port']))
        self.nodes[node]['CMDsocket'] = socketCmd
        self.nodes[node]['CMDs'] = r['CMDs']
        print(node, " sucesfully registed")
        return json.dumps({'OK': True})

    def register(self,arg=''):
        '''Call to parent registrar'''
        nodecmd = str(self.CMDs.keys())
        cmdjson=json.dumps({'node':self.nodename,\
           'host':self.myHost,\
           'port':self.myCmdPort,\
           'CMDs':nodecmd})
        cmd = '.registrar ' + cmdjson
        self.ParentCmdSocket.send(cmd)
        reply = json.loads(self.ParentCmdSocket.recv())
        if reply['OK']:
            print(self.nodename, " CMD PORT:", self.myCmdPort)
            print(self.nodename, " CMDs:", nodecmd)

    def deregister(self, arg):
        node = arg.strip()
        try:
            self.nodes[node]['CMDsocket'].close()
            self.nodes.pop(node, None)
        except:
            print("Fail closing CMD socket for node:", node)
        print("UNREGISTRING: " + node)
        return node+" UNREGISTRED"

    def end(self,arg=''):
        print("ENDING node:",self.nodename)
        '''end all childrennodes'''
        for node in self.nodes.keys():
            print("ASK TO END:", node)
            cmd = str('.end')
            socket=self.nodes[node]['CMDsocket']
            try:
                socket.send(cmd)
                reply = socket.recv()
                print(reply)
            except:
                print("ERROR Closing node:", node)
            finally:
                socket.close()

        '''Deregisting myshelf if I have parent'''
        if self.hasParent:
            try:
                cmd = str('.deregister ' + self.nodename)
                self.ParentCmdSocket.send(cmd)
                reply = self.ParentCmdSocket.recv()
                print(reply)
            except:
                print("Parent node is not available")
            finally:
                self.ParentCmdSocket.close()

        '''Now kill myshelf'''
        self.RUN = False
        self.myCmdSocket.close()
        print(self.nodename+": term zmqcontext")
        self.zmqcontext.term()
        
        print(self.nodename+": waiting CMDthread end")
        try:
                self.CMDThread.join()
        except:
                print("Can join thread:",self.CMDThread)

        print(self.nodename + "***ENDED***")
        return

    def run(self):
        '''Dummy. Normaly overloaded by a child class'''
        while self.RUN:
            time.sleep(1)
        print(self.nodename+" RUN ENDED")

    def signal_handler(self, signal, frame):
        print('You pressed Ctrl+C!')
        self.end()
        exit()

    def heartbeat(self, arg):
        '''heartbeat Parent part'''
        node = arg.strip()
        print("Received a heartBeat from a child class. node:", node)
        return True
    
    @threaded
    def nodeheartbeat(self):
        '''Child heartbeat part'''
        time.sleep(1)
        while self.RUN:
            for node in self.nodes.keys():
                cmd = str('.heartbeat ' + node)
                self.nodes[node]['CMDsocket'].send(cmd)
                time.sleep(1)
                reply = self.nodes[node]['CMDsocket'].recv()
                if reply:
                    print(node, "is alive")
                else:
                    print(node, "is death")


#Child class for testing
class test_class(node):
    pass


if __name__ == '__main__':
    port = 7770
    parent_host = 'localhost'
    parent_port = False
    e = test_class('test0','test', port, parent_host, parent_port)
    e.scanCMDs()
    e.run()
    exit()
