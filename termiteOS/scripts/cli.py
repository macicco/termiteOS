#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas

import click

@click.command()
@click.argument('yamlfile')
def launch(yamlfile):
    import termiteOS.launch as launch
    launch.launchmachine(yamlfile)


@click.command()
@click.option('--name', default='lx200', help='module name')
@click.option('--port', type=int, help='Port listen', default=6001)
@click.option('--parent_host', default='localhost', help='Parent host')
@click.option('--parent_port', type=int, help='Parent port', default=5000)
def lx200(name,port, parent_host, parent_port):
    import termiteOS.nodes.tcpproxy as tcpproxy
    tcpproxy.runtcpproxy(name,port, parent_host, parent_port)


@click.command()
@click.option('--name', default='joy0', help='module name')
@click.option('--host', default='localhost', help='Interface to listen')
@click.option('--port', type=int, help='Port listen', default=6002)
@click.option('--parent_host', default='localhost', help='Parent host')
@click.option('--parent_port', type=int, help='Parent port', default=5000)
def joystick(name,host, port, parent_host, parent_port):
    import termiteOS.nodes.joystick as joystick
    #click.echo("%s %u %s %u" % (host,port,parent_host,parent_port))
    joystick.runjoystick(name, port, parent_host, parent_port)


@click.command()
@click.option('--name', default='ROOTHUB', help='module name')
@click.option('--host', default='localhost', help='Interface to listen')
@click.option('--port', type=int, help='Port listen', default=5000)
@click.option('--parent_host', default='localhost', help='Parent host')
@click.option('--parent_port', type=int, help='Parent port', default=False)
def hub(name,host, port, parent_host, parent_port):
    import termiteOS.nodes.hub as hub
    #click.echo("%s %u %s %u" % (host,port,parent_host,parent_port))
    hub.runhub(name, port, parent_host, parent_port)

@click.command()
@click.option('--name', default='engine0', help='module name')
@click.option('--host', default='localhost', help='Interface to listen')
@click.option('--port', type=int, help='Port listen', default=5000)
@click.option('--parent_host', default='localhost', help='Parent host')
@click.option('--parent_port', type=int, help='Parent port', default=False)
def telescope(name,host, port, parent_host, parent_port):
    import termiteOS.nodes.telescope as telescope
    #click.echo("%s %u %s %u" % (host,port,parent_host,parent_port))
    telescope.runtelescope(name, port, parent_host, parent_port)
