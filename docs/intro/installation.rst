.. Documentation on installation

Installation
============

Install the PyMTL3 Framework
----------------------------

PyMTL3 requires >= Python3.6. We highly recommend working inside a virtual
environment. Here is how to create a virtual environment and install
:pypi:`PyMTL3 <pymtl3>` using ``pip``:

.. prompt:: bash $

    python3 -m venv pymtl3
    source pymtl3/bin/activate
    pip install pymtl3

.. note:: Your virtual environment will be deactivated when your current terminal
    session is termindated. To re-activate your PyMTL3 virtual environment:

    .. prompt:: bash $

        source pymtl3/bin/activate

    and to manually deactivate your current virtual environment:

    .. prompt:: bash $

        deactivate

Install the Verilator Simulator
-------------------------------

PyMTL3 optionally supports `Verilator <https://www.veripool.org/wiki/verilator>`_, an
open-source toolchain for compiling Verilog RTL models into C++ simulators, to co-simulate
Verilog modules with PyMTL3 components. We recommend compiling and installing the latest
Verilator from source because the standard package managers tend to host only the old
versions which lack some of the features that PyMTL3 uses. Here is how to compiling
the latest Verilator and setting it up to work with PyMTL3:

Acquire the necessary packages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will be using ``git`` to obtain the latest release of Verilator. In addition, PyMTL3
uses `cffi <https://cffi.readthedocs.io>`_ to communicate with the C++ simulator generated
by Verilator.

.. prompt:: bash $

   sudo apt-get install git python-dev libffi-dev

We also need the following packages to compile Verilator from source:

.. prompt:: bash $

   sudo apt-get install make autoconf g++ libfl-dev bison

Build and install Verilator
^^^^^^^^^^^^^^^^^^^^^^^^^^^

First retrieve the most recent stable Verilator release from the official git repo:

.. prompt:: bash $

   git clone https://git.veripool.org/git/verilator
   git pull
   git checkout stable

Next build and install Verilator:

.. prompt:: bash $

   autoconf
   ./configure
   make
   sudo make install

Verify that Verilator is on your ``PATH`` as follows:

.. prompt:: bash $

   verilator --version

Set up Verilator for PyMTL3
^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are two ways to set up Verilator for PyMTL3: using ``pkg-config`` or setting
environment variable ``PYMTL_VERILATOR_INCLUDE_DIR``. You may choose either one that
you feel is the most convenient.

Using ``pkg-config``
""""""""""""""""""""

Install ``pkg-config`` and verify that it is setup correctly as follows:

.. prompt:: bash $

   sudo apt-get install pkg-config
   pkg-config --variable=includedir verilator

If the output is a valid path to the include directory, you are all set. Otherwise
you may need to refer to the next section to set up the environment variable.

Using environment variable
""""""""""""""""""""""""""

If ``pkg-config`` is not able to provide the information of Verilator, environment
variable ``PYMTL_VERILATOR_INCLUDE_DIR`` needs to point to the include directory
of the installed Verilator. If you installed Verilator to the default path, the
following command will set up the variable. Replace the default path with your
custom include path if necessary.

.. prompt:: bash $

   export PYMTL_VERILATOR_INCLUDE_DIR="/usr/local/share/verilator/include"
