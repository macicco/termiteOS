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
status = True
PIDs = []

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
        except Exception as exc:
            result = str(exc)
            status = False
            print("FAIL:", result,func,*args)
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
    print("LAUNCHER:Launching node:" + name + " type:", nodetype)
    print("LAUNCHER:--> Host:", host, "Port:", port, "Parent Host:", parent_host,
          "Parent Port:", parent_port)
    i = importlib.import_module("termiteOS.nodes."+nodetype)
    fn_to_call = getattr(i, 'run' + nodetype)
    print("KKK::",elements.keys())
    if 'params' in elements.keys():
            params = elements['params']
            print("LAUNCHER:PARAMS",params)
            r=run_in_separate_process(fn_to_call, name, port, parent_host, parent_port,params)
    else:
            r=run_in_separate_process(fn_to_call, name, port, parent_host, parent_port)
    status = status and r
    if 'nodes' in elements.keys():
        print("LAUNCHER:--> Module:", name, " has chidrens. Launching..")
        for node in elements['nodes']:
            print("LAUNCHER:\n",node)
            status = status and launchnode(node, host, port)
    return status


def launchmachine(yamlfile):
    with open(yamlfile) as y:
        doc = y.read()
    try:
        ydoc = yaml.load(doc)
    except:
        print("LAUNCHER:malformed yaml:\n")
        print(doc)
        return False
    #print(ydoc)
    rtn = launchnode(ydoc)
    print("kill -9 "+" ".join(PIDs))
    return rtn


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("usage:" + sys.argv[0] + " yaml_file")
        exit(1)
    yamlfile = sys.argv[1]
    print("LAUNCHER:Reading from:" + yamlfile)
    print('LAUNCHER:',launchmachine(yamlfile))
