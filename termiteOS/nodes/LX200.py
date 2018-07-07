#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
'''
LX200 command set
socat TCP:localhost:6666,reuseaddr pty,link=/tmp/lx200
'''
from __future__ import print_function
import socket
import sys
import select
import time
from thread import *
import zmq
from termiteOS.config import *


context = zmq.Context()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def startserver(port):
	host=''
	print('Starting LX200 mount controler.')
	print('Socket created',host,":",str(port))

	#Bind socket to local host and port
	try:
	    s.bind((host, port))
	except socket.error as msg:
	    print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
	    sys.exit()
     
	print('Socket bind complete')
 
	#Start listening on socket
	s.listen(1)
	print('Socket now listening')
 


#End='something useable as an end marker'
def recv_end(conn):
    End='#'
    total_data=[]
    while True:
	    time.sleep(0.05)
    	    data=''

	    try:	
            	data=conn.recv(1)
	    except:
		print("socket close")
		cmd="SOCKET_CLOSE"	
		break

	    if data=='':
		cmd="SOCKET_CLOSE"	
		break

            if End in data:
                total_data.append(data[:data.find(End)])
		cmd=''.join(total_data).replace('\n','').replace('\r','')
		if len(cmd)==0:
			continue
		else:
			break
	    else:
            	total_data.append(data)

    #print "CMD parse:",repr(cmd)
    return cmd

#Function for handling connections. This will be used to create threads
def clientthread(conn,parent_host,parent_port):
    RUN=True
    #  Socket to talk to ZMQserver
    zmqSocket = context.socket(zmq.REQ)
    zmqSocket.connect("tcp://%s:%i" % (parent_host,parent_port))
    print("Connecting with hub %s:%i"% (parent_host,parent_port))

   
    #infinite loop so that function do not terminate and thread do not end.
    while RUN:
	    	cmd=recv_end(conn)
		if cmd == "SOCKET_CLOSE":
			break
		#print "<-",cmd
		zmqSocket.send(cmd)
		reply=zmqSocket.recv()
		#print "->",reply
    		conn.send(str(reply))


    #came out of loop
    #conn.shutdown(2)    # 0 = done receiving, 1 = done sending, 2 = both
    conn.close()
    print("Disconnecting..")
 
def runLX200(port,parent_host,parent_port):
	startserver(port)
	#now keep talking with the client
	RUN=True
	while RUN:
	  try:
	    #wait to accept a connection - blocking call
	    conn, addr = s.accept()
	    print('Connected with ' + addr[0] + ':' + str(addr[1]))
     	    #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
	    start_new_thread(clientthread ,(conn,parent_host,parent_port,))

	  except:
	    RUN=False
	
	s.close()


if __name__ == '__main__':
	runLX200(5001,'localhost',5000)
