#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas


from __future__ import print_function
import time, datetime
import zmq
import json
import logging
import signal
from termiteOS.config import *


class node(object):
    '''
    Node virtual class. Implements all comunication logic and basic functions.

    .. note:: For the derived class: self.CMDs is the command matrix. Call addCMD() after set.
              Commands starting with '.' work but are not showed.
              Also calling scanCMDS() add all class methods starting with 'cmd_' as a commands.
    '''
    def __init__(self, name, nodetype, port, parent_host, parent_port):
        #logging.basicConfig(filename=name+'.log',format='%(asctime)s %(levelname)s:'+name+' %(message)s',level=logging.DEBUG)
        logging.basicConfig(format='%(asctime)s %(levelname)s:'+name+' %(message)s',level=logging.INFO)
        logging.info("Creating node %s. node type:%s", name, nodetype)
        self.nodename = name
        self.nodetype = nodetype
        logging.info("%s listen CMDs on:%i",name, port)
        self.zmqcontext = zmq.Context()
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
            logging.info("HasParent parent at %s:%i Connecting..",parent_host, parent_port)
            self.hasParent = True
            self.hubCmdHost = parent_host
            self.hubCmdPort = parent_port
            self.ParentCmdSocket = self.zmqcontext.socket(zmq.REQ)
            self.ParentCmdSocket.connect(
                "tcp://%s:%i" % (self.hubCmdHost, self.hubCmdPort))
            self.register()
        else:
            #it is the hub itself
            logging.info("Node is a ROOT HUB")
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
        self.addCMDs(cmdvector)

    @threaded
    def zmqQueue(self):
        '''this thread listen and process all the CMD from other nodes. **Run in background** '''
        while self.RUN:
            if True:
                try:
                        address, empty, message = self.myCmdSocket.recv_multipart()
                        logging.debug("RECV CMD: %s", message)
                except:
                        self.myCmdSocket.close()
                        break

                '''
                Special case for .end command.
                Calling end() close all sockets so we have to answer before.
                '''
                if message == '.end':
                        reply='Last message from '+self.nodename+'. Closing socket'
                        logging.info(".end CMD: %s", reply)
                        self.myCmdSocket.send_multipart([
                                address,
                                b'',
                                str(reply),
                                ])
                        self.end()
                        break
                else:
                        #  Do some 'work'
                        reply = self.cmd(message)
                        logging.debug("SEND CMD response: %s", reply)
                        #  Send reply back to a specific client
                        self.myCmdSocket.send_multipart([
                                address,
                                b'',
                                str(reply),
                                ])
        logging.info("CMD LOOP END.")
        return

    def cmd(self, cmd):
        '''Execute the cmd command

           :param cmd: string contain the command with his parameters

           :returns: A message containing the answer
        '''
        for c in self.CMDs.keys():
            l = len(c)
            if (cmd[:l] == c):
                arg = cmd[l:].strip()
                return self.CMDs[c](arg)
                break

        return self.cmddummy(cmd)

    def cmddummy(self, arg):
        '''Default cmd to execute when not knowed cmd match. Do nothing'''
        logging.info("DUMMY CMD:%s", arg)
        return

    def cmd_help(self, arg):
        '''Print help text. Do nothing. Normaly overloaded by a child class'''
        string = "Base class. Do nothing"
        return string

    def cmd_ls(self,arg):
        '''list the node commands'''
        visibleCMDs = [ c for c in self.CMDs.keys() if not c.startswith('.')]
        string = "node:"+self.nodename+". TYPE:"+self.nodetype+"\n"
        string = string +"\tAvailable commands:\n"
        for cmd in visibleCMDs:
            string = string +'\t\t'+ cmd + "\n"
        return string

    def cmd_nodes(self,arg):
        '''
        list the children nodes:

        :param arg: (None)

        :returns: a python list  all children node names
        '''
        mod=[m for m in self.nodes.keys()]
        return mod

    def cmd_tree(self, arg):
        '''Print all self and children nodes availabled commands

        :param arg: (None)

        :returns: a string contain all commands
        '''
        r=[]
        for m in self.nodes.keys():
                a=(m+' ls').encode("utf8")
                reply=self.exenodeCmd(a)
                r.append(reply)
        return ''.join(r)


    def exenodeCmd(self, arg):
        '''Execute the command in the children'''
        s = arg.split()
        if len(s) == 0:
            return 0
        node = s[0]
        if not (node in self.nodes.keys()):
            logging.warn("External cmd on %s:Not such node",node)
            return 0
        cmd = arg[len(node):].strip()
        logging.info("exec:send %s to %s from %s", cmd, node,self.nodename)
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
        logging.info("REGISTER: node %s sucesfully registed",node)
        return json.dumps({'OK': True})

    def register(self,arg=''):
        '''Call to parent registrar'''
        logging.info("Asking parent to register")
        nodecmd = str(self.CMDs.keys())
        cmdjson=json.dumps({'node':self.nodename,\
           'host':self.myHost,\
           'port':self.myCmdPort,\
           'CMDs':nodecmd})
        cmd = '.registrar ' + cmdjson
        self.ParentCmdSocket.send(cmd)
        reply = json.loads(self.ParentCmdSocket.recv())
        if reply['OK']:
            logging.info("Registed at parent  %s:%i",self.hubCmdHost, self.hubCmdPort)


    def deregister(self, arg):
        '''Close the zmq socket and deleted node from the children list'''
        node = arg.strip()
        try:
            self.nodes[node]['CMDsocket'].close()
            self.nodes.pop(node, None)
        except:
            logging.warn("DEREGISTRING: Fail closing CMD socket for node:%s", node)
        logging.info("UNREGISTED: %s ", node)
        return node+" UNREGISTED"

    def end(self,arg=''):
        '''End all'''
        logging.info("ENDING node: %s",self.nodename)
        #end all childrennodes
        for node in self.nodes.keys():
            logging.info("ASK TO END: %s", node)
            cmd = str('.end')
            socket=self.nodes[node]['CMDsocket']
            try:
                socket.send(cmd)
                reply = socket.recv()
                logging.info(reply)
            except:
                logging.warn("ERROR Closing node:%s", node)
            finally:
                socket.close()

        #Unregisting myshelf if I have parent
        if self.hasParent:
            try:
                logging.info("Ask parent to unregister")
                cmd = str('.deregister ' + self.nodename)
                self.ParentCmdSocket.send(cmd)
                reply = self.ParentCmdSocket.recv()
                logging.info(reply)
            except:
                logging.warn("Parent node is not available")
            finally:
                self.ParentCmdSocket.close()

        #Now kill myshelf
        self.RUN = False
        self.myCmdSocket.close()
        logging.info("Term zmqcontext")
        self.zmqcontext.term()
        
        logging.info("Waiting CMDthread end")
        try:
                self.CMDThread.join()
        except:
                logging.warn("Can't join CMD thread")

        logging.info("***ENDED***")
        return

    def run(self):
        '''Dummy. Normaly overloaded by a child class'''
        while self.RUN:
            time.sleep(1)
        logging.info("MAIN LOOP RUN ENDED")

    def signal_handler(self, signal, frame):
        '''Capture Ctril+C key'''
        logging.info('You pressed Ctrl+C!')
        self.end()
        exit()

    def heartbeat(self, arg):
        '''heartbeat Parent part'''
        node = arg.strip()
        logging.info("Received a heartBeat from a child class. node:%s", node)
        return True

    def HasChildren(self):
        '''
        :Return: **True** if the node has childrens. **False** otherwise
        '''
        if len(self.nodes.keys())>0:
                return True
        else:
                return False

    def cmd_ping(self,arg):
        response={}
        if self.HasChildren():
            for node in self.nodes.keys():
                logging.info("ASK TO ping: %s", node)
                cmd = str('ping')
                socket=self.nodes[node]['CMDsocket']
                try:
                        socket.send(cmd)
                        reply = socket.recv()
                        logging.info(reply)
                        response[node]=reply
                except:
                        logging.warn("ERROR ping node %s", node)
        else:
                response[self.nodename]='pong'       
                logging.info("PING response:", response)         
                return response
                
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
                    logging.info("is alive")
                else:
                    logging.info("is death")


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
