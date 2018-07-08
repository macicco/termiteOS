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
import threading
import zmq
import termiteOS.moduleSkull as moduleSkull


context = zmq.Context()

class tcpproxy(moduleSkull.module):
        def __init__(self, name, port, parent_host, parent_port,params):
                super(tcpproxy, self).__init__(name, 'tcpproxy', port, parent_host, parent_port)
                self.parent_host=parent_host
                self.parent_port=parent_port
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                print(params)
                tcpport=int(params['tcpport'])
                print(tcpport)
                self.startserver(tcpport)

        def startserver(self,port):
                port=int(port)
                host = ''
                print('Starting tcpproxy.')
                print('Socket created', host, ":", str(port))

                #Bind socket to local host and port

                try:
                        self.s.bind((host, port))
                except socket.error as msg:
                        print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' +
                        msg[1])
                        sys.exit()

                print('Socket bind complete')

                #Start listening on socket
                self.s.listen(1)
                print('Socket now listening')



        def run(self):
                #now keep talking with the client
                while self.RUN:
                        try:
                                #wait to accept a connection - blocking call
                                conn, addr = self.s.accept()
                                print('Connected with ' + addr[0] + ':' + str(addr[1]))
                                #start newthread takes 1st argument as a function name to be run,
                                # second is the tuple of arguments to the function.
                                t = threading.Thread(target=self.clientthread, args=(
                                        conn,
                                        self.parent_host,
                                        self.parent_port,
                                        ))
                                t.start()
                        except:
                                self.RUN = False
                self.s.close()


        def recv_end(self,conn):
                #End='something useable as an end marker'
                End = '#'
                total_data = []
                while True:
                        time.sleep(0.05)
                        data = ''

                        try:
                                data = conn.recv(1)
                        except:
                                print("socket close")
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
            self.RUN = True
            #  Socket to talk to ZMQserver
            #zmqSocket = context.socket(zmq.REQ)
            #zmqSocket.connect("tcp://%s:%i" % (parent_host, parent_port))
            #print("Connecting with hub %s:%i" % (parent_host, parent_port))

            #infinite loop so that function do not terminate and thread do not end.
            while self.RUN:
                cmd = self.recv_end(conn)
                if cmd == "SOCKET_CLOSE":
                    break
                print("<-",cmd)
                self.socketHUBCmd.send(cmd)
                reply = self.socketHUBCmd.recv()
                print("->",reply)
                conn.send(str(reply))
        
            #came out of loop
            #conn.shutdown(2)    # 0 = done receiving, 1 = done sending, 2 = both
            conn.close()
            print("Disconnecting..")


def runtcpproxy(name,port, parent_host, parent_port,params):
        p=tcpproxy(name, port, parent_host, parent_port,params)
        p.run()
        return
        try:
                p.run()
        except:
                p.end()

if __name__ == '__main__':
    runtcpproxy('tcpproxy',5001, 'localhost', 5000,params={'tcpport':6000})

