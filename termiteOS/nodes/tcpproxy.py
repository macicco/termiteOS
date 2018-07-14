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
import logging
import socket
import sys
import select
import time
import threading
import zmq
import termiteOS.nodeSkull as nodeSkull


context = zmq.Context()

class tcpproxy(nodeSkull.node):
        def __init__(self, name, port, parent_host, parent_port,params):
                super(tcpproxy, self).__init__(name, 'tcpproxy', port, parent_host, parent_port)
                self.parent_host=parent_host
                self.parent_port=parent_port
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                tcpport=int(params['tcpport'])
                self.tcpport=tcpport
                if 'End' in params.keys():
                        self.End=params['End']
                else:
                        self.End='\n'
                logging.info('TCP SOCKET LISTEN ON PORT:%i',tcpport)
                self.startserver(tcpport)
                self.connections=[]


        def startserver(self,port):
                port=int(port)
                host = ''
                logging.info('Starting tcpproxy.')
                logging.info('Socket created %s:%i', host, port)

                #Bind socket to local host and port

                try:
                        self.s.bind((host, port))
                except socket.error as msg:
                        logging.error('Bind failed. Error Code : %i %s' , msg[0], msg[1])
                        sys.exit()

                logging.info('Socket bind complete')

                #Start listening on socket
                self.s.listen(1)
                logging.info('Socket now listening')



        def run(self):
                #now keep talking with the client
                while self.RUN:
                        try:
                                #wait to accept a connection - blocking call
                                conn, addr = self.s.accept()
                                logging.info('New TCP client %s:%i', addr[0],addr[1])
                                #start newthread takes 1st argument as a function name to be run,
                                # second is the tuple of arguments to the function.
                                if self.RUN:
                                        t = threading.Thread(target=self.clientthread, args=(
                                                conn,
                                                self.parent_host,
                                                self.parent_port,
                                                ))
                                        t.start()
                                        self.connections.append((conn,t))
                                else:
                                        logging.info('NOT RUN. Thread wasnt fired')
                                        break
                        except:
                                self.RUN = False
                self.s.close()
                logging.info('RUN END. Bind socket closed')


        def recv_end(self,conn):
                #End='something useable as an end marker'
                End = self.End
                total_data = []
                while True:
                        time.sleep(0.05)
                        data = ''

                        try:
                                data = conn.recv(1)
                        except:
                                logging.info("TCP socket close while reciving..")
                                cmd = "SOCKET_CLOSE"
                                break

                        if data == '':
                                cmd = "SOCKET_CLOSE"
                                break

                        if End in data:
                                total_data.append(data[:data.find(End)])
                                cmd = ''.join(total_data).replace('\n', '').replace('\r', '')
                                if len(cmd) == 0:
                                        continue
                                else:
                                        break
                        else:
                                total_data.append(data)

                return cmd


        #Function for handling connections. This will be used to create threads
        def clientthread(self,conn, parent_host, parent_port):

            #  Socket to talk to ZMQserver
            zmqSocket = context.socket(zmq.REQ)
            zmqSocket.connect("tcp://%s:%i" % (parent_host, parent_port))
            logging.info("Connecting with parent node ZMQ %s:%i", parent_host, parent_port)

            #infinite loop so that function do not terminate and thread do not end.
            while self.RUN:
                try:
                        cmd = self.recv_end(conn)
                except:
                        logging.info("TCP socket rcv error")
                        break

                if cmd == "SOCKET_CLOSE":
                    break
                if cmd == "quit":
                    break
                logging.info("<-%s",cmd)
                try:
                        self.ParentCmdSocket.send(cmd)
                except:
                        logging.info("Error sending to zmq")
                        break
                try:
                        reply = self.ParentCmdSocket.recv()
                except:
                        logging.info("Error sending to zmq")
                        break


                logging.info("->%s",reply)
                try:
                        conn.send(str(reply))
                except:
                        logging.info("TCP socket send error")
                        break
            #came out of loop
            #conn.shutdown(2)    # 0 = done receiving, 1 = done sending, 2 = both
            conn.close()
            zmqSocket.close()
            logging.info("Disconnecting..")

        def end(self, arg=''):
                self.RUN = False

                #Hack to exit run loop blocked by 'socket.accept'
                ss=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                ss.connect( ('localhost', self.tcpport))
                ss.close()
                #self.s.close()
             
                for c,thrd in self.connections:
                        c.close()
                        thrd.join(1)
                logging.info("TCP connections and Threads ended")                
                super(tcpproxy, self).end()
                logging.info("----ENDED----") 


def runtcpproxy(name,port, parent_host, parent_port,params):
        p=tcpproxy(name, port, parent_host, parent_port,params)
        p.run()
        return
        try:
                p.run()
        except:
                p.end()

if __name__ == '__main__':
    runtcpproxy('tcpproxy0',5001, 'localhost', 5000,params={'tcpport':6000})

