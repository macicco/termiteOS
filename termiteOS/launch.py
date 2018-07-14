#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas

from __future__ import print_function
from __future__ import with_statement


import sys,time
import yaml
import importlib
import os
import logging
status = True
PIDs = []
# create logger
logger = logging.getLogger('simple_example')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s %(levelname)s:LAUNCHER  %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


def run_in_separate_process(func, *args, **kwds):
    global PIDs
    pid = os.fork()
    if pid > 0:
        status = True
        PIDs.append(str(pid))
    else:
        try:
            result = func(*args, **kwds)
            status = True
            os._exit(0)
        except Exception as exc:
            result = str(exc)
            status = False
            logger.info("FAIL:%s", result)
        #os._exit(status)
    time.sleep(1)
    return status


def launchnode(nodedict, parent_host='', parent_port=False):
    global status, PIDs
    name = list(nodedict.keys())[0]
    elements = nodedict[name]
    nodetype = elements['type']
    host = elements['host']
    port = elements['port']
    logger.info("Launching node: %s type: %s",name, nodetype)
    logger.info("--> %s on %s:%i connected with %s:%i as parent",name, host, port,parent_host,parent_port)
    i = importlib.import_module("termiteOS.nodes."+nodetype)
    fn_to_call = getattr(i, 'run' + nodetype)
    if 'params' in elements.keys():
            params = elements['params']
            logger.info("PARAMS: %s",params)
            r=run_in_separate_process(fn_to_call, name, port, parent_host, parent_port,params)
    else:
            r=run_in_separate_process(fn_to_call, name, port, parent_host, parent_port)
    status = status and r
    if 'nodes' in elements.keys():
        logger.info("--> Module %s  has chidrens. Launching..", name)
        for node in elements['nodes']:
            logger.info("launching: ",node)
            status = status and launchnode(node, host, port)
    return status


def launchmachine(yamlfile):
    with open(yamlfile) as y:
        doc = y.read()
    try:
        ydoc = yaml.load(doc)
    except:
        logger.info("malformed yaml:\n")
        logger.info(doc)
        return False
    #logger.info(ydoc)
    rtn = launchnode(ydoc)
    logger.info("kill -9 "+" ".join(PIDs))
    return rtn


if __name__ == '__main__':
    if len(sys.argv) != 2:
        logger.info("usage: %s yaml_file",sys.argv[0])
        exit(1)
    yamlfile = sys.argv[1]
    logger.info("Reading from:%s" , yamlfile)

