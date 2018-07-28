#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas

import click

@click.command()
@click.argument('yamlfile')
def launch(yamlfile):
    """Launch all nodes defined in YAMLFILE"""
    import termiteOS.launch as launch
    launch.launchmachine(yamlfile)

@click.command()
@click.option('--port', type=int, help='Port to connect', default=5000)
def console(port):
    """Launch a termiteOS console"""
    import termiteOS.nodes.console as console
    console.console(port)

@click.command()
@click.option('--name', default='telescope0', help='module name')
@click.option('--port', type=int, help='Port listen', default=5000)
@click.option('--parent_host', default='localhost', help='Parent host to connect to. If False the node become a ROOTHUB')
@click.option('--parent_port', type=int, help='Parent port to connect to', default=False)
def telescope(name, port, parent_host, parent_port):
    """Launch a telescope node"""
    import termiteOS.nodes.telescope as telescope
    #click.echo("%s %u %s %u" % (host,port,parent_host,parent_port))
    telescope.runtelescope(name, port, parent_host, parent_port)

@click.command()
@click.option('--name', default='tcpproxy0', help='module name')
@click.option('--port', type=int, help='Port listen', default=5001)
@click.option('--parent_host', default='localhost', help='Parent host to connect to. If False the node become a ROOTHUB')
@click.option('--parent_port', type=int, help='Parent port to connect to', default=5000)
@click.option('--params', help='Dictionary with extra parameters default={"tcpport":6001,"End":"#"}', default='{"tcpport":6001,"End":"#"}')
def tcpproxy(name,port, parent_host, parent_port,params):
    """Launch a tcpproxy node"""
    import ast
    import termiteOS.nodes.tcpproxy as tcpproxy
    params=ast.literal_eval(params)
    tcpproxy.runtcpproxy(name,port, parent_host, parent_port,params)

@click.command()
@click.option('--name', default='TLEtracker0', help='module name')
@click.option('--port', type=int, help='Port listen', default=5002)
@click.option('--parent_host', default='localhost', help='Parent host to connect to. If False the node become a ROOTHUB')
@click.option('--parent_port', type=int, help='Parent port to connect to', default=5000)
def TLEtracker(name, port, parent_host, parent_port):
    """Launch a TLEtracker node"""
    import termiteOS.nodes.TLEtracker as TLEtracker
    #click.echo("%s %u %s %u" % (host,port,parent_host,parent_port))
    TLEtracker.runTLEtracker(name, port, parent_host, parent_port)


@click.command()
@click.option('--name', default='joy0', help='module name')
@click.option('--port', type=int, help='Port listen', default=5003)
@click.option('--parent_host', default='localhost', help='Parent host to connect to. If False the node become a ROOTHUB')
@click.option('--parent_port', type=int, help='Parent port to connect to', default=5000)
def joystick(name, port, parent_host, parent_port):
    """Launch a joystick node"""
    import termiteOS.nodes.joystick as joystick
    #click.echo("%s %u %s %u" % (host,port,parent_host,parent_port))
    joystick.runjoystick(name, port, parent_host, parent_port)


@click.command()
@click.option('--name', default='ROOTHUB', help='module name')
@click.option('--port', type=int, help='Port listen', default=5000)
@click.option('--parent_host', default='localhost', help='Parent host to connect to. If False the node become a ROOTHUB')
@click.option('--parent_port', type=int, help='Parent port to connect to', default=False)
def hub(name, port, parent_host, parent_port):
    """Launch a hub node"""
    import termiteOS.nodes.hub as hub
    #click.echo("%s %u %s %u" % (host,port,parent_host,parent_port))
    hub.runhub(name, port, parent_host, parent_port)

