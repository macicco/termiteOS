Nodes
=====

Nodes are separate programs. The nodes communicate each other using the zmq protocol. The organization between the nodes is hierarchical thus a node can have several children but has only one parent or none in the case of the'root node'.

Nodes are based on http://zeromq.org/ for transport and on https://developers.google.com/protocol-buffers/ for message definitions and serialization.

Each node has its own ZMQ port and a set of commands and responds to through that port. Each node opens connections with its parent node and with all its children so that messages can be exchanged.

These nodes can run on the same or different CPUs taking advantage of all the features of the ZMQ protocol.

All nodes are derive from nodeSkull base class which implements all the comunication logic and basic commands.

.. toctree::
   :maxdepth: 2
   :glob:

   node_*

Node commands
-------------

.. toctree::
   :maxdepth: 2
   :glob:

   cmd_*



