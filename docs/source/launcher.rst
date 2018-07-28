Launcher
________

* **Launcher** program launch a set of node following the instruction in yaml file

This program allow to launch at once all nodes needed for a specific hardware/funtionality.

Example of a yaml configuration file:

.. code-block:: yaml

   simple:
    type: telescope
    host: localhost
    port: 5000
    nodes:
       - LX200:
            type: tcpproxy
            host: localhost
            port: 5001
            params: {'tcpport':6001,'End':'#'}
       - tracker:
            type: TLEtracker
            host: localhost
            port: 5002
            nodes:
               - trackertcp:
                    type: tcpproxy
                    host: localhost
                    port: 5003
                    params: {'tcpport':6003}

This example is equivalent to run on the command shell all following commands:

.. code-block:: bash

   miteTelescope   --port 5000 --name simple
   mitetcpproxy    --port 5001 --name LX200 --parent_host localhost --parent_port 5000 --params {'tcpport':6001,'End':'#'}
   miteTLEtracker  --port 5002 --name tracker --parent_host localhost --parent_port 5000
   mitetcpproxy    --port 5003 --name trackertcp --parent_host localhost --parent_port 5002 --params {'tcpport':6003}




You can find other examples in 'termoteOS/machines/' 

Command line:
^^^^^^^^^^^^^

.. click:: termiteOS.scripts.cli:launch
   :prog: miteLaunch
   :show-nested:



API
^^^

.. automodule:: termiteOS.launch
   :members:
   :undoc-members:
   :inherited-members:

