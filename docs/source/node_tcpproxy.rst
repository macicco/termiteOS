tcpproxy
________

* **tcproxy** node acts as a proxy connector between other node and an especific TCP port

All commands recived throught the TCP port are relay to the myCmdPort port of the node conected to. 

Using this node allow us to connect to a specific node (the parent node of tcpproxy node) with a regular `telnet host port`

Command line:
^^^^^^^^^^^^^

.. click:: termiteOS.scripts.cli:tcpproxy
   :prog: mitetcpproxy
   :show-nested:

.. include:: cmd_tcpproxy.rst
