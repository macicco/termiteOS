#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas

import click

@click.command()
@click.argument('count', type=int, metavar='N')
def cli(count):
    """Echo a value `N` number of times"""
    for i in range(count):
        click.echo("Tum!")

@click.command()
@click.option('--host', default='localhost',help='Interface to listen')
@click.option('--port', type=int,help='Port listen',default=7777)
@click.option('--parent_host', default='localhost',help='Parent host')
@click.option('--parent_port', type=int,help='Parent port',default=7778)
def lx200(host,port,parent_host,parent_port):
	import termiteOS.nodes.LX200 as LX200
	LX200.LX200(host,port)


@click.command()
@click.option('--host', default='localhost',help='Interface to listen')
@click.option('--port', type=int,help='Port listen',default=7777)
@click.option('--parent_host', default='localhost',help='Parent host')
@click.option('--parent_port', type=int,help='Parent port',default=7778)
def joystick(host,port,parent_host,parent_port):
	import termiteOS.nodes.joystick as joystick
	#click.echo("%s %u %s %u" % (host,port,parent_host,parent_port))
	joystick.joystick()

@click.command()
@click.option('--host', default='localhost',help='Interface to listen')
@click.option('--port', type=int,help='Port listen',default=7777)
@click.option('--parent_host', default='localhost',help='Parent host')
@click.option('--parent_port', type=int,help='Parent port',default=7778)
def hub(host,port,parent_host,parent_port):
	import termiteOS.nodes.engine as engine
	#click.echo("%s %u %s %u" % (host,port,parent_host,parent_port))
	engine.hub(host,port)
