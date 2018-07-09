#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
'''
General propose console to termiteOS
'''
import zmq
import cmd, sys


context = zmq.Context()

class termiteShell(cmd.Cmd):
        intro = 'Welcome to the termiteOS shell.   Type help or ? to list commands.\n'
        prompt = '(termite) '
        def do_hello(self):
                'Say Hello'
                print("Hello")
        def do_exit(self,arg):
                'Say bye'
                print("Bye")
                exit(0)



def console(port):
        zmqSocket = context.socket(zmq.REQ)
        zmqSocket.connect("tcp://localhost:%i" % port)
        while True:
	        cmd = raw_input('>')
	        zmqSocket.send(cmd)
	        reply=zmqSocket.recv()
	        print reply
        print "Disconnecting.."
        zmqSocket.close()


if __name__ == '__main__':
        shell=termiteShell()
        shell.cmdloop()

