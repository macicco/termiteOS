#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas

from __future__ import print_function
from __future__ import with_statement

import sys
import yaml
from termiteOS.nodes import *
import os
status = True
PIDs = []


def run_in_separate_process(func, *args, **kwds):
    global PIDs
    pid = os.fork()
    PIDs.append(str(pid))
    if pid > 0:
        status = True
    else:
        try:
            result = func(*args, **kwds)
            status = True
        except Exception, exc:
            result = exc
            status = False
            print("FAIL:", result)
        #os._exit(status)
    return status


def launchnode(nodedict, parent_host='', parent_port=False):
    global status, PIDs
    name = nodedict.keys()[0]
    elements = nodedict[name]
    nodetype = elements['type']
    host = elements['host']
    port = elements['port']
    print("Launching node:" + name + " type:", nodetype)
    print("--> Host:", host, "Port:", port, "Parent Host:", parent_host,
          "Parent Port:", parent_port)
    fn_to_call = getattr(globals()[nodetype], 'run' + nodetype)
    status = status and run_in_separate_process(fn_to_call, name, port,
                                                parent_host, parent_port)
    if 'nodes' in elements.keys():
        print("--> Module:", name, " has chidrens. Launching..")
        for node in elements['nodes']:
            status = status and launchnode(node, host, port)
    return status


def launchmachine(yamlfile):
    with open(yamlfile) as y:
        doc = y.read()
        print(doc)
    try:
        ydoc = yaml.load(doc)
    except:
        print("Launch:malformed yaml \n" + doc)
    #print(ydoc)
    rtn = launchnode(ydoc)
    print(" ".join(PIDs))
    return rtn


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("usage:" + sys.argv[0] + " yaml_file")
        exit(1)
    yamlfile = sys.argv[1]
    print("Reading from:" + yamlfile)
    print(launchmachine(yamlfile))
